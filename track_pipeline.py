from copy import copy
import csv
from itertools import count
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import ezdxf
from ezdxf import units

from DXF_to_lapdata import (
    TRACKDATA_FIELDS, arc_sweep, export_geometry_excel, extract_segments,
    geometry_rows, reset_direction, sort_segments,
)
from cone_to_ini import write_cone_ini
from lapdata_to_xy import DEFAULT_XY_SPACING, XY_FIELDS, export_xy, xy_rows
from track_characterization import plot_analysis


def read_dxf(path):
    drawing = ezdxf.readfile(path)
    entities = list(drawing.modelspace().query("LINE ARC CIRCLE"))
    if not entities:
        raise ValueError("這份 DXF 的模型空間沒有直線（LINE）、圓弧（ARC）或圓形（CIRCLE）。")
    layers = sorted({entity.dxf.layer for entity in entities if entity.dxftype() != "CIRCLE"},
                    key=str.casefold)
    try:
        scale = units.conversion_factor(drawing.units, units.M)
        source = "依 DXF 的單位換算"
    except (TypeError, ValueError):
        if path.resolve() == Path(__file__).with_name("fsae_A_2025.dxf").resolve():
            scale, source = 0.1, "依內附 FSAE A 2025 範例的原比例"
        else:
            scale, source = 1.0, "DXF 無可用單位，請確認比例"
    return entities, layers, scale, source


def circle_centers(circles, layer=None):
    points = []
    for circle in circles:
        if layer is not None and circle.dxf.layer != layer:
            continue
        center = circle.ocs().to_wcs(circle.dxf.center)
        if not (math.isfinite(center.x) and math.isfinite(center.y)):
            raise ValueError("圓心包含無效的 XY 座標，請檢查 DXF。")
        points.append((center.x, center.y))
    return points


def prepare_route(entities, layer=None, endpoint_tolerance=1e-8):
    if not math.isfinite(endpoint_tolerance) or endpoint_tolerance <= 0:
        raise ValueError("端點容差必須是大於零的數字。")
    selected = [
        entity for entity in entities
        if entity.dxftype() in ("LINE", "ARC") and (layer is None or entity.dxf.layer == layer)
    ]
    for entity in selected:
        if entity.dxftype() == "ARC" and not entity.dxf.extrusion.isclose((0, 0, 1)):
            raise ValueError("賽道路徑含有不同平面的圓弧，請先將圖元轉成 XY 平面。")

    segments = extract_segments(selected)
    if not segments or any(not math.isfinite(segment_length(seg)) or segment_length(seg) <= 0 for seg in segments):
        raise ValueError("賽道路徑是空的，或包含長度無效的路段。")
    ordered = sort_segments(segments.copy(), tol=endpoint_tolerance)
    if len(ordered) != len(segments):
        raise ValueError(f"只接上 {len(ordered)}／{len(segments)} 段。請檢查圖層、端點間隙或多餘的輔助線。")
    if math.dist(ordered[-1].end, ordered[0].start) >= endpoint_tolerance:
        raise ValueError("路徑沒有閉合。請檢查最後一段是否接回起點。")
    return ordered


def segment_length(segment):
    if segment.type == "LINE":
        return math.dist(segment.start, segment.end)
    return segment.radius * abs(arc_sweep(segment))


def order_from_start(segments, start, reverse=False):
    if not 1 <= start <= len(segments):
        raise ValueError("起跑段超出範圍。")
    route = [copy(segment) for segment in segments[start - 1:] + segments[:start - 1]]
    if reverse:
        reset_direction(route)
    return route


def scaled_track_rows(segments, start, reverse, scale):
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("每單位公尺數必須是大於零的數字。")

    route = order_from_start(segments, start, reverse)
    for segment in route:
        segment.start = tuple(value * scale for value in segment.start)
        segment.end = tuple(value * scale for value in segment.end)
        if segment.center is not None:
            segment.center = tuple(value * scale for value in segment.center)
            segment.radius *= scale
    rows = geometry_rows(route)
    total = sum(row["length"] for row in rows)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("換算後的賽道長度無效，請檢查比例。")
    return rows, total


def analyze_track(segments, start, reverse, scale, lateral_g):
    validate_lateral_g(lateral_g)
    rows, total = scaled_track_rows(segments, start, reverse, scale)
    return plot_analysis(rows, lateral_g=lateral_g), total


def validate_lateral_g(lateral_g):
    if not math.isfinite(lateral_g) or lateral_g <= 0:
        raise ValueError("橫向加速度必須是大於零的數字。")


def export_track(segments, start, reverse, scale, output_folder, stem, export_format, lateral_g=1.6,
                 *, xy_spacing=None, xy_points_per_segment=None, ini_options=None):
    rows, total = scaled_track_rows(segments, start, reverse, scale)
    if xy_spacing is None and xy_points_per_segment is None:
        xy_spacing = DEFAULT_XY_SPACING
    xy_options = {"spacing": xy_spacing, "points_per_segment": xy_points_per_segment}

    output_folder = Path(output_folder)
    figure = None
    with TemporaryDirectory(prefix=".track-", dir=output_folder) as staging:
        base = Path(staging) / stem
        if export_format == "excel":
            geometry = base.with_name(f"{stem}_geometry.xlsx")
            coordinates = base.with_name(f"{stem}_coordinates_xy.xlsx")
            export_geometry_excel(rows, geometry)
            export_xy(rows, coordinates, **xy_options)
            staged = (geometry, coordinates)
        elif export_format == "csv":
            geometry = base.with_name(f"{stem}_geometry.csv")
            coordinates = base.with_name(f"{stem}_coordinates_xy.csv")
            write_csv(geometry, TRACKDATA_FIELDS, ([row[field] for field in TRACKDATA_FIELDS] for row in rows))
            write_csv(coordinates, XY_FIELDS, xy_rows(rows, **xy_options))
            staged = (geometry, coordinates)
        elif export_format == "analysis":
            image = base.with_name(f"{stem}_track_analysis.png")
            validate_lateral_g(lateral_g)
            figure = plot_analysis(rows, lateral_g=lateral_g)
            figure.savefig(image, dpi=160)
            staged = (image,)
        elif export_format == "ini":
            ini = base.with_name(f"{stem}_cones.ini")
            points = ((x, y) for _, x, y in xy_rows(rows, **xy_options))
            write_cone_ini(ini, points, **(ini_options or {}))
            staged = (ini,)
        else:
            raise ValueError(f"不支援的輸出格式：{export_format}")
        files = publish_files(staged, output_folder)
    return files, figure, total


def export_circle_centers(centers, scale, output_folder, stem, export_format, *, ini_options=None):
    if not centers:
        raise ValueError("所選圖層沒有圓形可匯出。")
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("每單位公尺數必須是大於零的數字。")
    points = [(x * scale, y * scale) for x, y in centers]
    if any(not (math.isfinite(x) and math.isfinite(y)) for x, y in points):
        raise ValueError("換算後的圓心座標無效，請檢查比例。")

    output_folder = Path(output_folder)
    with TemporaryDirectory(prefix=".track-", dir=output_folder) as staging:
        folder = Path(staging)
        if export_format == "csv":
            target = folder / f"{stem}_circle_centers.csv"
            write_csv(target, XY_FIELDS, ((index, x, y) for index, (x, y) in enumerate(points, start=1)))
        elif export_format == "ini":
            target = folder / f"{stem}_circle_cones.ini"
            write_cone_ini(target, points, **(ini_options or {}))
        else:
            raise ValueError(f"圓心不支援此輸出格式：{export_format}")
        return publish_files((target,), output_folder)[0]


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


def publish_files(staged, folder):
    for version in count(1):
        suffix = "" if version == 1 else f"_{version}"
        reserved = []
        try:
            for source in staged:
                target = folder / f"{source.stem}{suffix}{source.suffix}"
                with target.open("xb"):
                    reserved.append(target)
        except OSError as exc:
            for target in reserved:
                target.unlink()
            if isinstance(exc, FileExistsError):
                continue
            raise
        break

    try:
        for source, target in zip(staged, reserved):
            source.replace(target)
    except OSError:
        for target in reserved:
            target.unlink()
        raise
    return reserved

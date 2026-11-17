"""Run the desktop DXF pipeline inside the browser worker."""

import base64
from io import BytesIO
import json
import os
from pathlib import Path
<<<<<<< HEAD
import re
=======
>>>>>>> 62778b8eb98f41e0b8dcc8191be6eacc9d45ca39
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

os.environ["MPLBACKEND"] = "Agg"

from DXF_to_lapdata import arc_sweep
from lapdata_to_xy import sample_arc
from track_pipeline import (
    analyze_track, circle_centers, export_circle_centers, export_track, order_from_start,
    prepare_route, read_dxf,
)


<<<<<<< HEAD
# The shared pipeline also serves the Chinese desktop interface.
SCALE_SOURCE_LABELS = {
    "依 DXF 的單位換算": "Converted from the DXF units.",
    "依內附 FSAE A 2025 範例的原比例": "Using the original scale of the bundled FSAE A 2025 sample.",
    "DXF 無可用單位，請確認比例": "The DXF has no usable units. Verify the scale.",
}

ERROR_MESSAGES = {
    "這份 DXF 的模型空間沒有直線（LINE）、圓弧（ARC）或圓形（CIRCLE）。":
        "The DXF model space contains no LINE, ARC, or CIRCLE entities.",
    "圓心包含無效的 XY 座標，請檢查 DXF。":
        "A circle center has invalid XY coordinates. Check the DXF file.",
    "端點容差必須是大於零的數字。": "Endpoint tolerance must be greater than zero.",
    "賽道路徑含有不同平面的圓弧，請先將圖元轉成 XY 平面。":
        "The track contains arcs outside the XY plane. Move the track entities to the XY plane.",
    "賽道路徑是空的，或包含長度無效的路段。":
        "The track path is empty or contains segments with invalid lengths.",
    "路徑沒有閉合。請檢查最後一段是否接回起點。":
        "The track is open. Check that the last segment connects back to the start.",
    "起跑段超出範圍。": "The starting segment number is out of range.",
    "每單位公尺數必須是大於零的數字。": "Meters per DXF unit must be greater than zero.",
    "換算後的賽道長度無效，請檢查比例。": "The scaled track length is invalid. Check the scale.",
    "橫向加速度必須是大於零的數字。": "Lateral acceleration must be greater than zero.",
    "所選圖層沒有圓形可匯出。": "There are no circles to export from the selected layers.",
    "換算後的圓心座標無效，請檢查比例。": "The scaled circle centers are invalid. Check the scale.",
    "XY 點距必須是大於零的數字。": "XY sample spacing must be greater than zero.",
    "XY 點距太小，請增加點距。": "The XY sample spacing is too small. Increase the spacing.",
    "請選擇一種 XY 取樣方式。": "Choose one XY sampling method.",
    "每段點數必須是至少 2 的整數，以保留兩端。":
        "Enter a whole number of at least 2 points per segment to include both endpoints.",
}

ERROR_PATTERNS = (
    (
        r"只接上 (\d+)／(\d+) 段。請檢查圖層、端點間隙或多餘的輔助線。",
        r"Connected only \1 of \2 track segments. Check the selected layer, endpoint gaps, or extra construction lines.",
    ),
    (
        r"取樣會超過 Excel 的列數上限（([\d,]+) 點）。請降低密度或改用 CSV。",
        r"Sampling would produce \1 points and exceed Excel's row limit. Reduce the sampling density or export CSV.",
    ),
    (r"不支援的輸出格式：(.+)", r"Unsupported export format: \1"),
    (r"圓心不支援此輸出格式：(.+)", r"Unsupported circle center export format: \1"),
)


def english_error_message(message):
    if message in ERROR_MESSAGES:
        return ERROR_MESSAGES[message]
    for pattern, replacement in ERROR_PATTERNS:
        match = re.fullmatch(pattern, message)
        if match:
            return match.expand(replacement)
    return message


=======
>>>>>>> 62778b8eb98f41e0b8dcc8191be6eacc9d45ca39
def download(name, data, media_type):
    return {"filename": name, "type": media_type, "data": base64.b64encode(data).decode("ascii")}


def route_preview(route):
    segments = []
    for segment in route:
        if segment.type == "ARC":
            xs, ys = sample_arc(segment.center, segment.radius, segment.start_angle, arc_sweep(segment), 48)
            points = list(zip(xs.tolist(), ys.tolist()))
        else:
            points = [segment.start, segment.end]
        segments.append({"type": segment.type, "points": points})
    return segments


class Drawing:
    def __init__(self):
        self.route = []

    def load(self, path, filename):
        entities, layers, scale, source = read_dxf(Path(path))
        self.entities = entities
        self.circles = [entity for entity in entities if entity.dxftype() == "CIRCLE"]
        self.stem = Path(filename.replace("\\", "_").replace("/", "_")).stem or "track"
        self.route = []
        return {
<<<<<<< HEAD
            "layers": layers, "scale": scale, "scaleSource": SCALE_SOURCE_LABELS.get(source, source),
=======
            "layers": layers, "scale": scale, "scaleSource": source,
>>>>>>> 62778b8eb98f41e0b8dcc8191be6eacc9d45ca39
            "circleLayers": sorted({circle.dxf.layer for circle in self.circles}, key=str.casefold),
            "circleCount": len(self.circles),
        }

    def prepare(self, layer, tolerance):
        self.route = []
        self.route = prepare_route(self.entities, layer, tolerance)
        return route_preview(self.route)

    def order(self, start, reverse):
        return route_preview(order_from_start(self.route, start, reverse))

    def centers(self, layer):
        return circle_centers(self.circles, layer)

    def analysis(self, start, reverse, scale, lateral_g):
        figure, total = analyze_track(self.route, start, reverse, scale, lateral_g)
        data = BytesIO()
        figure.savefig(data, format="png", dpi=160)
        return {
            "total": total,
            **download(f"{self.stem}_track_analysis.png", data.getvalue(), "image/png"),
        }

    def export(self, mode, export_format, scale, layer=None, start=1, reverse=False,
               spacing=None, points_per_segment=None, ini_options=None):
        with TemporaryDirectory() as folder:
            if mode == "circle":
                path = export_circle_centers(self.centers(layer), scale, folder, self.stem,
                                             export_format, ini_options=ini_options)
                media_type = "text/csv" if export_format == "csv" else "text/plain"
                return download(path.name, path.read_bytes(), media_type)

            paths, _, _ = export_track(self.route, start, reverse, scale, folder, self.stem, export_format,
                                       xy_spacing=spacing, xy_points_per_segment=points_per_segment,
                                       ini_options=ini_options)
            if len(paths) == 1:
                return download(paths[0].name, paths[0].read_bytes(), "text/plain")
            data = BytesIO()
            with ZipFile(data, "w", compression=ZIP_DEFLATED) as archive:
                for path in paths:
                    archive.write(path, arcname=path.name)
            return download(f"{self.stem}_{export_format}.zip", data.getvalue(), "application/zip")


drawing = Drawing()
operations = {
    "load": drawing.load,
    "prepare": drawing.prepare,
    "order": drawing.order,
    "centers": drawing.centers,
    "analysis": drawing.analysis,
    "export": drawing.export,
}


def dispatch(operation, args):
<<<<<<< HEAD
    try:
        result = operations[operation](**json.loads(args))
    except ValueError as error:
        original = str(error)
        message = english_error_message(original)
        if message == original:
            raise
        raise ValueError(message) from None
    return json.dumps(result, allow_nan=False)
=======
    return json.dumps(operations[operation](**json.loads(args)), allow_nan=False)
>>>>>>> 62778b8eb98f41e0b8dcc8191be6eacc9d45ca39

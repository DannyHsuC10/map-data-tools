"""Run the desktop DXF pipeline inside the browser worker."""

import base64
from io import BytesIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

os.environ["MPLBACKEND"] = "Agg"

from DXF_to_lapdata import arc_sweep
from lapdata_to_xy import sample_arc
from track_pipeline import (
    analyze_track, circle_centers, export_circle_centers, export_track, order_from_start,
    prepare_route, read_dxf,
)


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
            "layers": layers, "scale": scale, "scaleSource": source,
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
    return json.dumps(operations[operation](**json.loads(args)), allow_nan=False)

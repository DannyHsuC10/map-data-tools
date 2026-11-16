import math

import numpy as np
from openpyxl import Workbook

from DXF_to_lapdata import read_trackdata


XY_FIELDS = ("Point", "X", "Y")
DEFAULT_XY_SPACING = 1.0
DEFAULT_XY_POINTS = 5
EXCEL_MAX_DATA_ROWS = 1_048_575  # Leave one row for the header.


def sample_arc(center, radius, start, sweep, count):
    angles = np.linspace(start, start + sweep, count)
    return center[0] + radius * np.cos(angles), center[1] + radius * np.sin(angles)


def row_coordinates(row, arc_points=5):
    if row["Type"] == "LINE":
        return (row["Start_X"], row["End_X"]), (row["Start_Y"], row["End_Y"])
    start, sweep = arc_angles(row)
    return sample_arc((row["Center_X"], row["Center_Y"]), row["Radius"], start, sweep, arc_points)


def arc_angles(row):
    start = math.radians(row["Start_Angle (deg)"])
    end = math.radians(row["End_Angle (deg)"])
    sweep = (end - start) % math.tau
    if row["Direction"] == "Clockwise":
        sweep -= math.tau
    return start, sweep


def distance_intervals(total, spacing):
    if not math.isfinite(spacing) or spacing <= 0:
        raise ValueError("XY 點距必須是大於零的數字。")
    ratio = total / spacing
    if not math.isfinite(ratio):
        raise ValueError("XY 點距太小，請增加點距。")
    intervals = max(1, math.ceil(ratio))
    if intervals > 1 and abs(total - (intervals - 1) * spacing) <= 4 * math.ulp(total):
        intervals -= 1
    return intervals


def interpolate(row, fractions):
    start_x, start_y = row["Start_X"], row["Start_Y"]
    end_x, end_y = row["End_X"], row["End_Y"]
    if row["Type"] == "LINE":
        for fraction in fractions:
            yield start_x + (end_x - start_x) * fraction, start_y + (end_y - start_y) * fraction
    else:
        start, sweep = arc_angles(row)
        cx, cy, radius = row["Center_X"], row["Center_Y"], row["Radius"]
        for fraction in fractions:
            angle = start + sweep * fraction
            yield cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def coordinates_by_segment(rows, intervals):
    yield rows[0]["Start_X"], rows[0]["Start_Y"]
    for row in rows:
        yield from interpolate(row, (index / intervals for index in range(1, intervals)))
        yield row["End_X"], row["End_Y"]


def coordinates_by_distance(rows, spacing, intervals):
    yield rows[0]["Start_X"], rows[0]["Start_Y"]
    segment_start = 0.0
    point_index = 1
    for row in rows:
        length = row["length"]
        segment_end = segment_start + length
        first_index = point_index
        while point_index < intervals and point_index * spacing <= segment_end:
            point_index += 1
        fractions = ((index * spacing - segment_start) / length for index in range(first_index, point_index))
        yield from interpolate(row, fractions)
        segment_start = segment_end
    yield rows[-1]["End_X"], rows[-1]["End_Y"]


def xy_rows(rows, *, spacing=None, points_per_segment=None, max_points=None):
    segments = [row for row in rows if row["Type"] in ("LINE", "ARC")]
    if not segments:
        return
    if spacing is not None and points_per_segment is not None:
        raise ValueError("請選擇一種 XY 取樣方式。")
    if points_per_segment is not None:
        if not isinstance(points_per_segment, int) or points_per_segment < 2:
            raise ValueError("每段點數必須是至少 2 的整數，以保留兩端。")
        intervals = points_per_segment - 1
        point_count = 1 + len(segments) * intervals
        coordinates = coordinates_by_segment(segments, intervals)
    elif spacing is not None:
        # Use the same cumulative arithmetic here and when locating sample stations.
        total = 0.0
        for row in segments:
            total += row["length"]
        intervals = distance_intervals(total, spacing)
        point_count = intervals + 1
        coordinates = coordinates_by_distance(segments, spacing, intervals)
    else:
        point_count = sum(2 if row["Type"] == "LINE" else 5 for row in segments)
        coordinates = (point for row in segments for point in zip(*row_coordinates(row)))
    if max_points is not None and point_count > max_points:
        raise ValueError(f"取樣會超過 Excel 的列數上限（{point_count:,} 點）。請降低密度或改用 CSV。")
    for index, (x, y) in enumerate(coordinates, start=1):
        yield index, float(x), float(y)


def export_xy(rows, filename, *, spacing=None, points_per_segment=None):
    wb = Workbook()
    sheet = wb.active
    sheet.append(XY_FIELDS)
    for row in xy_rows(rows, spacing=spacing, points_per_segment=points_per_segment, max_points=EXCEL_MAX_DATA_ROWS):
        sheet.append(row)
    wb.save(filename)


def main():
    import matplotlib.pyplot as plt

    rows = read_trackdata("fsae_A_2025_track.xlsx")
    output = "fsae_A_2025_track_xy.xlsx"
    export_xy(rows, output)
    print(f"Coordinates saved to {output}")
    _, ax = plt.subplots()
    for row in rows:
        if row["Type"] not in ("LINE", "ARC"):
            continue
        color = "tab:blue" if row["Type"] == "LINE" else "tab:red"
        ax.plot(*row_coordinates(row, arc_points=100), color=color)
        ax.scatter(*row_coordinates(row), color=color, s=10)
    ax.set(aspect="equal", title="Track Geometry", xlabel="X", ylabel="Y")
    ax.grid(True)
    plt.show()


if __name__ == "__main__":
    main()

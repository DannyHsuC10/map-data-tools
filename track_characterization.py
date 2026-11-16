import numpy as np
from matplotlib.figure import Figure

from DXF_to_lapdata import read_trackdata


def plot_analysis(rows, figure=None, lateral_g=1.6):
    if figure is None:
        figure = Figure(figsize=(12, 8), layout="constrained")

    lengths = np.array([row["length"] for row in rows], dtype=float)
    radii = np.array([row["Radius"] or 0 for row in rows], dtype=float)
    corners = np.array([row["Type"] == "ARC" for row in rows])
    curvature = np.zeros(len(rows))
    curvature[corners] = 1 / radii[corners]
    curvature[[row["Direction"] == "Clockwise" for row in rows]] *= -1
    distances = np.r_[0, np.cumsum(lengths)]
    arc_radii = radii[corners]
    arc_lengths = lengths[corners]
    arc_times = arc_lengths / np.sqrt(lateral_g * 9.81 * arc_radii)

    axes = figure.subplots(3, 2)
    curvature_ax, count_ax, length_ax, time_ax, frequency_ax, wavelength_ax = axes.flat
    curvature_ax.stairs(curvature, distances, color="#075985")
    curvature_ax.set(title="Track curvature", xlabel="Distance (m)", ylabel="Curvature (1/m)")

    bins = np.histogram_bin_edges(arc_radii, bins=50)
    for ax, weights, title, ylabel in (
        (count_ax, None, "Corner radius distribution", "Count"),
        (length_ax, arc_lengths, "Length-weighted radii", "Arc length (m)"),
        (time_ax, arc_times, "Time-weighted radii", "Estimated time (s)"),
    ):
        ax.set(title=title, xlabel="Corner radius (m)", ylabel=ylabel)
        if arc_radii.size:
            counts, _, bars = ax.hist(arc_radii, bins=bins, weights=weights, color="#0e7490")
            if weights is not None:
                for index in np.argsort(counts)[-5:]:
                    if counts[index] > 0:
                        bars[index].set_facecolor("#c2410c")
        else:
            ax.text(0.5, 0.5, "No arcs", ha="center", va="center", transform=ax.transAxes)

    # Uniform samples along the whole lap preserve the distance of short segments.
    count = max(2, int(min(200_000, distances[-1] / 0.5)))
    ds = distances[-1] / count
    indices = np.searchsorted(distances[1:], np.arange(count) * ds, side="right")
    spectrum = np.abs(np.fft.rfft(curvature[indices]))[1:]
    frequencies = np.fft.rfftfreq(count, d=ds)[1:]
    frequency_ax.plot(frequencies, spectrum, color="#0e7490", marker="." if len(spectrum) == 1 else None)
    frequency_ax.set(title="Curvature spectrum (FFT)", xlabel="Spatial frequency (1/m)", ylabel="Amplitude")
    wavelength_ax.plot(1 / frequencies, spectrum, color="#0e7490", marker="." if len(spectrum) == 1 else None)
    wavelength_ax.set(title="Curvature by wavelength", xlabel="Spatial wavelength (m)", ylabel="Amplitude", xscale="log")
    for ax in axes.flat:
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    return figure


def main():
    import matplotlib.pyplot as plt

    rows = read_trackdata("fsae_A_2025_track.xlsx")
    figure = plot_analysis(rows, plt.figure(figsize=(12, 8), layout="constrained"))
    for ax, label, unit in ((figure.axes[2], "長度", "m"), (figure.axes[3], "估算時間", "s")):
        bars = [bar for bar in ax.patches if bar.get_height() > 0]
        print(f"{label}權重排名（彎道合計 {sum(bar.get_height() for bar in bars):.2f} {unit}）")
        for bar in sorted(bars, key=lambda item: item.get_height(), reverse=True)[:5]:
            radius = bar.get_x() + bar.get_width() / 2
            print(f"{radius:.2f} m | weight = {bar.get_height():.2f} {unit}")
    plt.show()


if __name__ == "__main__":
    main()

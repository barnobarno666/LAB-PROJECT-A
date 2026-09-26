"""Plot one-factor slices through the best sampled four-factor grid case."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator


HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "four_factor_grid_search.csv"
SUMMARY_PATH = HERE / "optimization_summary.json"
OUTPUT_DIR = HERE

INK = "#202b39"
NAVY = "#0A2540"
RUBY = "#B82601"
MUTED = "#625e5a"
RULE = "#d8d2ca"
PAPER = "#fffdf9"

FACTORS = (
    {
        "key": "h2_co_molar_ratio",
        "stem": "h2_co_ratio",
        "title": r"$\mathrm{H_2/CO}$ feed ratio",
        "xlabel": r"Inlet $\mathrm{H_2/CO}$ molar ratio",
        "xformat": "%.1f",
        "yformat": "%.1f",
        "xticks": (1, 2, 3, 4, 5),
    },
    {
        "key": "inlet_temperature_c",
        "stem": "inlet_temperature",
        "title": "Inlet temperature",
        "xlabel": r"Inlet temperature, $T_{\mathrm{in}}$ ($^\circ$C)",
        "xformat": "%.0f",
        "yformat": "%.3f",
        "xticks": (250, 300, 350, 400),
    },
    {
        "key": "inlet_pressure_bar_abs",
        "stem": "inlet_pressure",
        "title": "Inlet pressure",
        "xlabel": r"Inlet pressure, $P_{\mathrm{in}}$ (bar abs)",
        "xformat": "%.0f",
        "yformat": "%.6f",
        "xticks": (5, 7, 9, 12, 15),
    },
    {
        "key": "catalyst_space_time_kg_s_mol_co",
        "stem": "catalyst_space_time",
        "title": "Catalyst space time",
        "xlabel": (
            r"$W_{\mathrm{cat}}/F_{\mathrm{CO,in}}$ "
            r"(kg$_{\mathrm{cat}}$ s mol$_{\mathrm{CO}}^{-1}$)"
        ),
        "xformat": "%.0f",
        "yformat": "%.2f",
        "xticks": (10, 40, 70, 100, 140),
    },
)


def _read_inputs() -> tuple[list[dict[str, str]], dict[str, float]]:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    optimum = summary["best_grid_case"]
    with CSV_PATH.open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    return records, optimum


def _same_setting(record: dict[str, str], optimum: dict[str, float], varied_key: str) -> bool:
    if record["status"] != "completed":
        return False
    for factor in FACTORS:
        key = factor["key"]
        if key == varied_key:
            continue
        if abs(float(record[key]) - float(optimum[key])) > 1e-8:
            return False
    return True


def _slice(
    records: list[dict[str, str]],
    optimum: dict[str, float],
    factor: dict[str, object],
) -> tuple[list[float], list[float]]:
    key = str(factor["key"])
    selected = [
        row
        for row in records
        if _same_setting(row, optimum, key)
        and (key != "inlet_pressure_bar_abs" or float(row[key]) >= 5.0)
    ]
    selected.sort(key=lambda row: float(row[key]))
    if not selected:
        raise RuntimeError(f"No completed grid cases found for {key}.")

    x = [float(row[key]) for row in selected]
    y = [float(row["outlet_co_conversion_pct"]) for row in selected]
    expected_optimum_y = float(optimum["outlet_co_conversion_pct"])
    optimum_index = min(range(len(x)), key=lambda index: abs(x[index] - float(optimum[key])))
    if abs(y[optimum_index] - expected_optimum_y) > 1e-8:
        raise RuntimeError(f"The {key} slice does not reproduce the recorded grid maximum.")
    factor["selected_count"] = len(selected)
    factor["optimum_x"] = float(optimum[key])
    factor["optimum_y"] = y[optimum_index]
    return x, y


def _fixed_conditions(varied_key: str, optimum: dict[str, float]) -> str:
    terms = []
    if varied_key != "h2_co_molar_ratio":
        terms.append(rf"$\mathrm{{H_2/CO}}={float(optimum['h2_co_molar_ratio']):.1f}$")
    if varied_key != "inlet_temperature_c":
        terms.append(
            rf"$T_{{\mathrm{{in}}}}={float(optimum['inlet_temperature_c']):.0f}^\circ\mathrm{{C}}$"
        )
    if varied_key != "inlet_pressure_bar_abs":
        terms.append(
            rf"$P_{{\mathrm{{in}}}}={float(optimum['inlet_pressure_bar_abs']):.0f}$ bar abs"
        )
    if varied_key != "catalyst_space_time_kg_s_mol_co":
        space_time = float(optimum["catalyst_space_time_kg_s_mol_co"])
        terms.append(
            rf"$W_{{\mathrm{{cat}}}}/F_{{\mathrm{{CO,in}}}}={space_time:.1f}$ "
            r"kg$_{\mathrm{cat}}$ s mol$_{\mathrm{CO}}^{-1}$"
        )
    return "   |   ".join(terms)


def _configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["CMU Serif", "Computer Modern Roman", "DejaVu Serif"],
            "mathtext.fontset": "cm",
            "font.size": 9.0,
            "axes.labelsize": 9.2,
            "axes.titlesize": 10.2,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 7.8,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": "#292929",
            "axes.linewidth": 0.85,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "xtick.major.size": 4.0,
            "ytick.major.size": 4.0,
            "xtick.minor.size": 2.2,
            "ytick.minor.size": 2.2,
            "xtick.major.width": 0.75,
            "ytick.major.width": 0.75,
            "xtick.minor.width": 0.55,
            "ytick.minor.width": 0.55,
            "axes.unicode_minus": False,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def _draw_axis(
    ax: plt.Axes,
    factor: dict[str, object],
    optimum: dict[str, float],
    x: list[float],
    y: list[float],
    panel_letter: str | None,
) -> None:
    key = str(factor["key"])
    ax.plot(
        x,
        y,
        color=NAVY,
        linewidth=1.7,
        marker="o",
        markersize=2.5,
        markerfacecolor=NAVY,
        markeredgewidth=0,
        zorder=3,
    )
    ax.scatter(
        [float(factor["optimum_x"])],
        [float(factor["optimum_y"])],
        s=58,
        marker="o",
        facecolor=PAPER,
        edgecolor=RUBY,
        linewidth=1.6,
        zorder=5,
    )

    if panel_letter:
        ax.set_title(
            f"({panel_letter})  {factor['title']}",
            loc="left",
            fontweight="bold",
            pad=25,
        )
        ax.text(
            0.0,
            1.025,
            _fixed_conditions(key, optimum),
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=7.2,
            color=MUTED,
            clip_on=False,
        )

    ax.set_xlabel(str(factor["xlabel"]), labelpad=6)
    ax.set_ylabel(r"Outlet CO conversion, $X_{\mathrm{CO}}$ (%)", labelpad=6)
    ax.xaxis.set_major_formatter(FormatStrFormatter(str(factor["xformat"])))
    ax.set_xticks(factor["xticks"])
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.yaxis.set_major_formatter(FormatStrFormatter(str(factor["yformat"])))
    ax.minorticks_on()
    ax.set_axisbelow(True)
    ax.grid(axis="y", which="major", color=RULE, linewidth=0.5, alpha=0.72)
    ax.tick_params(which="both", direction="in", top=True, right=True)

    if key == "h2_co_molar_ratio":
        ax.set_xlim(0.85, 5.15)
    elif key == "inlet_temperature_c":
        ax.set_xlim(240, 410)
    elif key == "inlet_pressure_bar_abs":
        ax.set_xlim(4.5, 15.5)
    else:
        ax.set_xlim(5, 145)

    low, high = min(y), max(y)
    span = high - low
    margin = max(0.12 * span, 1e-8)
    upper = min(100.35, high + margin)
    ax.set_ylim(max(0.0, low - margin), upper)


def _save_figure(fig: plt.Figure, stem: str, dpi: int = 400) -> None:
    for suffix in (".png", ".svg", ".pdf"):
        output_path = OUTPUT_DIR / f"{stem}{suffix}"
        fig.savefig(
            output_path,
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.06,
            facecolor=PAPER,
        )
        if suffix == ".svg":
            lines = output_path.read_text(encoding="utf-8").splitlines()
            output_path.write_text(
                "\n".join(line.rstrip() for line in lines) + "\n",
                encoding="utf-8",
            )
    plt.close(fig)


def main() -> None:
    _configure_style()
    records, optimum = _read_inputs()
    slices = {str(factor["key"]): _slice(records, optimum, factor) for factor in FACTORS}

    fig, axes = plt.subplots(2, 2, figsize=(13.2, 8.4), sharey=False)
    fig.text(
        0.075,
        0.975,
        "One-factor sensitivity at the grid-search best case",
        ha="left",
        va="top",
        fontsize=16.0,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.076,
        0.928,
        "Each panel varies one input while the other three remain at their best sampled settings.",
        ha="left",
        va="top",
        fontsize=9.0,
        color=MUTED,
    )
    fig.subplots_adjust(left=0.085, right=0.985, top=0.815, bottom=0.145, wspace=0.30, hspace=0.58)

    for index, (ax, factor) in enumerate(zip(axes.flat, FACTORS)):
        x, y = slices[str(factor["key"])]
        _draw_axis(ax, factor, optimum, x, y, "abcd"[index])

    fig.text(
        0.075,
        0.045,
        "Open circle: best sampled value for that input. Vertical scales are panel-specific and zoomed. "
        "Pressure is shown only over the 5–15 bar fitted kinetic range.",
        ha="left",
        va="bottom",
        fontsize=8.0,
        color=MUTED,
    )
    _save_figure(fig, "one_factor_sensitivities_2x2")

    for factor in FACTORS:
        x, y = slices[str(factor["key"])]
        fig, ax = plt.subplots(figsize=(7.2, 5.0))
        fig.text(
            0.09,
            0.97,
            f"Outlet CO conversion vs. {factor['title']}",
            ha="left",
            va="top",
            fontsize=14.0,
            fontweight="bold",
            color=INK,
        )
        fig.text(
            0.09,
            0.91,
            _fixed_conditions(str(factor["key"]), optimum),
            ha="left",
            va="top",
            fontsize=8.2,
            color=MUTED,
        )
        fig.subplots_adjust(left=0.135, right=0.975, top=0.81, bottom=0.19)
        _draw_axis(ax, factor, optimum, x, y, None)
        pressure_note = (
            "Pressure values are restricted to the 5–15 bar fitted kinetic range. "
            if factor["key"] == "inlet_pressure_bar_abs"
            else ""
        )
        fig.text(
            0.09,
            0.045,
            pressure_note
            + "Open circle: best sampled value. The vertical axis is zoomed to show this slice.",
            ha="left",
            va="bottom",
            fontsize=8.0,
            color=MUTED,
        )
        _save_figure(fig, f"sensitivity_{factor['stem']}")

    counts = ", ".join(f"{factor['stem']}={factor['selected_count']}" for factor in FACTORS)
    print(f"Wrote combined and standalone sensitivity figures to {OUTPUT_DIR}")
    print(f"Completed grid points in slices: {counts}")


if __name__ == "__main__":
    main()

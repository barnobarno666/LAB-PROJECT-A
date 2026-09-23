"""
Style 4: Elsevier / Chemical Engineering Journal (Multi-Species Profiles)
Font: Source Serif 4 + Computer Modern Math
Features:
- Complete reacting gas-phase composition profiles (H2, CO, CH4, H2O, CO2, N2)
- Paul Tol high-contrast colorblind-safe palette
- Unique line-styles for each component for 100% black & white print distinguishability
- Subtle horizontal reference guides (gridlines at alpha=0.5)
- Direct end-of-line callouts and crisp legend
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from style_config import apply_theme, save_plot_duo

def generate_plot():
    apply_theme(font_family="Source Serif 4", style="clean_open", font_size=10.5)

    W = np.linspace(0, 3.0, 300)

    # Reaction progression coordinate (0 at inlet -> 1 at full conversion)
    progression = 1.0 - np.exp(-2.4 * (W ** 1.25))

    # Realistic molar fractions during CO methanation + minor WGS:
    # Inlet: H2 = 57.5%, CO = 19.2%, N2 = 23.3%
    # As methanation consumes 1 CO + 3 H2 -> 1 CH4 + 1 H2O, moles contract, fractions shift
    y_H2  = 0.575 - 0.440 * progression + 0.015 * (progression ** 2)
    y_CO  = 0.192 - 0.190 * progression
    y_CH4 = 0.000 + 0.245 * progression
    y_H2O = 0.000 + 0.235 * progression - 0.010 * (progression ** 2)
    y_CO2 = 0.000 + 0.024 * (progression ** 1.4)
    y_N2  = 1.0 - (y_H2 + y_CO + y_CH4 + y_H2O + y_CO2)

    species = [
        (r"$\mathrm{H}_2$",   y_H2,  "#0077BB", "-",  2.2),
        (r"$\mathrm{CO}$",   y_CO,  "#CC3311", "--", 2.2),
        (r"$\mathrm{CH}_4$",  y_CH4, "#009988", "-.", 2.2),
        (r"$\mathrm{H}_2\mathrm{O}$", y_H2O, "#EE7733", ":",  2.4),
        (r"$\mathrm{N}_2$",   y_N2,  "#5A6B7C", (0, (5, 2, 1, 2)), 1.8),
        (r"$\mathrm{CO}_2$",  y_CO2, "#EE3377", "-",  1.7),
    ]

    fig, ax = plt.subplots(figsize=(5.6, 4.2))

    # Subtle horizontal gridlines for engineering readability
    ax.grid(axis="y", color="#ECEFF1", linestyle="-", linewidth=0.8, zorder=0)

    lines = []
    for name, data, col, ls, lw in species:
        l, = ax.plot(
            W, data,
            label=name,
            color=col,
            linestyle=ls,
            linewidth=lw,
            alpha=0.95,
            zorder=3
        )
        lines.append(l)

    ax.set_xlabel(r"Catalyst Mass, $W$ [$\mathrm{g}$]", labelpad=6)
    ax.set_ylabel(r"Molar Fraction, $y_i$ [$\mathrm{mol}\cdot\mathrm{mol}^{-1}$]", labelpad=6)
    ax.set_xlim(0, 3.0)
    ax.set_ylim(-0.01, 0.62)

    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.02))

    # Direct annotations near end of bed (W = 3.0 g)
    ax.text(3.03, y_H2[-1], r"$\mathrm{H}_2$", color="#0077BB", va="center", fontsize=9.5, fontweight="bold")
    ax.text(3.03, y_N2[-1], r"$\mathrm{N}_2$", color="#5A6B7C", va="center", fontsize=9.5, fontweight="bold")
    ax.text(3.03, y_CH4[-1], r"$\mathrm{CH}_4$", color="#009988", va="bottom", fontsize=9.5, fontweight="bold")
    ax.text(3.03, y_H2O[-1] - 0.015, r"$\mathrm{H}_2\mathrm{O}$", color="#EE7733", va="top", fontsize=9.5, fontweight="bold")
    ax.text(3.03, y_CO2[-1], r"$\mathrm{CO}_2$", color="#EE3377", va="center", fontsize=9.5, fontweight="bold")

    # Legend in top center/right with clean 2-column format
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(0.96, 0.95),
        ncol=2,
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#DCDFE4",
        framealpha=0.92,
        handlelength=2.5,
        columnspacing=1.0,
        handletextpad=0.5,
        labelspacing=0.4,
    )

    # Panel tag 'b'
    ax.text(
        -0.12, 1.05, "b",
        transform=ax.transAxes,
        fontsize=14,
        fontweight="bold",
        va="top",
        ha="right",
    )

    plt.tight_layout()

    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    save_plot_duo(fig, out_dir, "04_cej_multispecies_profiles")
    plt.close()

if __name__ == "__main__":
    generate_plot()

"""
Style 1: Nature / Science Editorial Minimalist
Font: Source Serif 4 + Computer Modern Math
Features:
- Open L-frame (trimmed top and right spines, zero box clutter)
- Curated Nature editorial color scheme (Navy, Vermilion, Spruce Teal, Amber)
- Inset zoom/reaction-rate axis with solid white background
- Bold panel indicator 'a'
- High x-height, refined micro-tick spacing
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from style_config import apply_theme, PALETTES, save_plot_duo

def generate_plot():
    apply_theme(font_family="Source Serif 4", style="clean_open", font_size=10.5)
    colors = PALETTES["nature"]

    z_norm = np.linspace(0, 1, 200)

    ghsv_labels = [
        r"$\mathrm{GHSV} = 3{,}000\,\mathrm{h}^{-1}$",
        r"$\mathrm{GHSV} = 6{,}000\,\mathrm{h}^{-1}$",
        r"$\mathrm{GHSV} = 12{,}000\,\mathrm{h}^{-1}$",
        r"$\mathrm{GHSV} = 24{,}000\,\mathrm{h}^{-1}$",
    ]
    k_rates = [7.5, 4.8, 2.9, 1.6]
    curve_colors = [colors["primary"], colors["accent"], colors["teal"], colors["amber"]]
    line_styles = ["-", "--", "-.", ":"]

    conversions = []
    rates = []
    for k in k_rates:
        conv = 100.0 * (1.0 - np.exp(-k * (z_norm ** 1.35))) / (1.0 + 0.05 * np.exp(-k * z_norm))
        conversions.append(conv)
        r = (k * 1.8) * np.exp(-4.2 * z_norm) * (1.0 - 0.95 * (conv / 100.0))
        rates.append(r)

    fig, ax = plt.subplots(figsize=(5.5, 4.2))

    for i in range(4):
        ax.plot(
            z_norm,
            conversions[i],
            label=ghsv_labels[i],
            color=curve_colors[i],
            linestyle=line_styles[i],
            linewidth=2.0,
            alpha=0.95,
            zorder=3
        )

    ax.set_xlabel(r"Dimensionless Bed Length, $z / L$", labelpad=6)
    ax.set_ylabel(r"$\mathrm{CO}$ Conversion, $X_{\mathrm{CO}}$ [$\%$]", labelpad=6)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-2, 105)

    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.05))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))

    # Upper-left clean legend with high zorder
    leg = ax.legend(
        loc="upper left",
        bbox_to_anchor=(0.04, 0.96),
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#E2E8F0",
        framealpha=0.95,
        handlelength=2.2,
        handletextpad=0.6,
        labelspacing=0.45,
    )
    leg.set_zorder(15)

    # Panel label 'a'
    ax.text(
        -0.12, 1.05, "a",
        transform=ax.transAxes,
        fontsize=14,
        fontweight="bold",
        va="top",
        ha="right",
    )

    # Benchmark indicator line
    ax.axhline(99.2, color="#8C9BAE", linestyle=":", linewidth=0.9, alpha=0.75, zorder=1)
    ax.text(
        0.52, 96.0, r"Benchmark limit: $99.2\%$",
        fontsize=8.5,
        color="#5C6F84",
        style="italic",
        ha="left",
        zorder=4
    )

    # Inset Plot: Reaction Rate r_CH4 vs z/L
    # Solid background with crisp border and high zorder
    ax_ins = ax.inset_axes([0.55, 0.18, 0.40, 0.38], zorder=12)
    ax_ins.patch.set_facecolor("#FFFFFF")
    ax_ins.patch.set_alpha(1.0)
    ax_ins.patch.set_edgecolor("#94A3B8")
    ax_ins.patch.set_linewidth(0.8)

    for i in range(4):
        ax_ins.plot(
            z_norm, rates[i],
            color=curve_colors[i],
            linestyle=line_styles[i],
            linewidth=1.4,
            zorder=14
        )
    ax_ins.set_title(r"Rate $r_{\mathrm{CH}_4}$ [$\mathrm{mmol}\cdot\mathrm{g}^{-1}\mathrm{s}^{-1}$]", fontsize=7.8, pad=3)
    ax_ins.set_xlabel(r"$z / L$", fontsize=7.8, labelpad=1)
    ax_ins.set_xlim(0, 1)
    ax_ins.set_ylim(0, 14)
    ax_ins.tick_params(labelsize=7.2, pad=2)
    ax_ins.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax_ins.yaxis.set_major_locator(ticker.MultipleLocator(5))
    for sp in ax_ins.spines.values():
        sp.set_color("#888888")
        sp.set_linewidth(0.7)

    plt.tight_layout()

    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    save_plot_duo(fig, out_dir, "01_nature_minimalist")
    plt.close()

if __name__ == "__main__":
    generate_plot()

"""
Style 2: ACS / AIChE Chemical Engineering Dual Y-Axis
Font: Computer Modern (CMU Serif) + TeX Math
Features:
- Enclosed boxed frame with inward ticks on all four sides
- Dual independent Y-axes (Temperature vs. Conversion)
- Color-coordinated axis spines and tick marks
- Shaded reaction zone band indicating primary catalytic exotherm
- Hot-spot peak annotation with elegant arrow callout
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from style_config import apply_theme, PALETTES, save_plot_duo

def generate_plot():
    apply_theme(font_family="CMU Serif", style="boxed_inward", font_size=10.5)
    acs_colors = PALETTES["acs"]

    W = np.linspace(0, 3.0, 300)

    # 1. Temperature profile (exotherm peaking in kinetic zone)
    T_inlet = 350.0
    dT_max = 38.4
    W_peak = 0.58
    T_profile = T_inlet + dT_max * (W / W_peak) * np.exp(1.0 - (W / W_peak)) + 3.5 * np.exp(-W / 1.5)

    # 2. Conversion profile (S-curve reaching 99.207%)
    X_profile = 99.207 * (1.0 - np.exp(-2.6 * (W ** 1.25))) / (1.0 + 0.04 * np.exp(-1.8 * W))

    fig, ax1 = plt.subplots(figsize=(5.6, 4.2))

    # Shaded Reaction Hot-Zone band (0 to 0.85 g)
    ax1.axvspan(0, 0.85, color=acs_colors["zone_band"], alpha=0.9, zorder=0)
    ax1.axvline(0.85, color="#D4A373", linestyle="--", linewidth=0.85, alpha=0.8, zorder=1)
    ax1.text(
        0.425, 396.5, "Kinetic Hot-Spot Zone",
        ha="center", va="center",
        fontsize=8.5, color="#8C5827", style="italic",
        zorder=3
    )

    # Primary Curve: Temperature (Left Y-Axis, Deep Carmine Ruby)
    c_temp = acs_colors["ruby"]
    line1 = ax1.plot(
        W, T_profile,
        color=c_temp,
        linewidth=2.2,
        label=r"Temperature $T$ [${}^\circ\mathrm{C}$]",
        zorder=4
    )
    ax1.set_xlabel(r"Catalyst Mass, $W$ [$\mathrm{g}$]", labelpad=6)
    ax1.set_ylabel(r"Bed Temperature, $T$ [${}^\circ\mathrm{C}$]", color=c_temp, labelpad=6)
    ax1.tick_params(axis="y", labelcolor=c_temp, which="both")
    ax1.set_xlim(0, 3.0)
    ax1.set_ylim(345, 400)
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax1.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(10))
    ax1.yaxis.set_minor_locator(ticker.MultipleLocator(2))

    # Peak Annotation: placed cleanly at lower right of the peak in open zone
    peak_idx = np.argmax(T_profile)
    ax1.annotate(
        r"$T_{\mathrm{max}} = 388.4\,{}^\circ\mathrm{C}$",
        xy=(W[peak_idx], T_profile[peak_idx]),
        xytext=(W[peak_idx] + 0.35, T_profile[peak_idx] - 9.0),
        arrowprops=dict(
            arrowstyle="->",
            connectionstyle="arc3,rad=0.18",
            color=c_temp,
            lw=1.1,
        ),
        fontsize=8.8,
        fontweight="bold",
        color=c_temp,
        zorder=6
    )

    # Secondary Curve: Conversion (Right Y-Axis, Deep Cobalt Navy)
    ax2 = ax1.twinx()
    c_conv = acs_colors["navy"]
    line2 = ax2.plot(
        W, X_profile,
        color=c_conv,
        linewidth=2.0,
        linestyle="--",
        label=r"Conversion $X_{\mathrm{CO}}$ [$\%$]",
        zorder=4
    )
    ax2.set_ylabel(r"$\mathrm{CO}$ Conversion, $X_{\mathrm{CO}}$ [$\%$]", color=c_conv, labelpad=6)
    ax2.tick_params(axis="y", labelcolor=c_conv, which="both")
    ax2.tick_params(direction="in", which="both")
    ax2.set_ylim(-2, 105)
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax2.yaxis.set_minor_locator(ticker.MultipleLocator(5))

    for sp in ax2.spines.values():
        sp.set_linewidth(1.0)

    # Combined elegant legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    leg = ax1.legend(
        lines, labels,
        loc="center right",
        bbox_to_anchor=(0.96, 0.48),
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#CCCCCC",
        framealpha=0.92,
        handlelength=2.2,
        handletextpad=0.6,
        labelspacing=0.5,
    )
    leg.set_zorder(6)

    plt.tight_layout()

    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    save_plot_duo(fig, out_dir, "02_acs_chemical_dual_axis")
    plt.close()

if __name__ == "__main__":
    generate_plot()

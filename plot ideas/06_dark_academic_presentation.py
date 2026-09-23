"""
Style 6: Dark Academic / High-Contrast Presentation (Beamer / OLED)
Font: Computer Modern (CMU Serif) + TeX Math
Features:
- Deep obsidian and charcoal background (#0E1117 / #161B22)
- Luminous high-contrast neon palette (Electric Cyan, Mint, Cyber Amber, Coral)
- Crisp platinum typography and subtle dark gridlines
- Tailored for dark-mode conference presentations, keynote talks, and defense slides
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from style_config import apply_theme, PALETTES, save_plot_duo

def generate_plot():
    apply_theme(font_family="CMU Serif", style="dark_mode", font_size=10.5)
    dk = PALETTES["dark_academic"]

    W = np.linspace(0, 3.0, 250)

    # 4 reaction temperatures (300, 325, 350, 375 C)
    temps = [r"$300\,{}^\circ\mathrm{C}$", r"$325\,{}^\circ\mathrm{C}$", r"$350\,{}^\circ\mathrm{C}$", r"$375\,{}^\circ\mathrm{C}$"]
    rates = [1.2, 1.9, 2.8, 4.4]
    glow_colors = [dk["cyan"], dk["mint"], dk["amber"], dk["coral"]]

    fig, ax = plt.subplots(figsize=(5.6, 4.2))

    # Plot curves with slight glow effect
    for T_lbl, k, col in zip(temps, rates, glow_colors):
        X = 99.3 * (1.0 - np.exp(-k * (W ** 1.30))) / (1.0 + 0.04 * np.exp(-k * W))
        ax.plot(W, X, color=col, linewidth=5.2, alpha=0.18, zorder=3)
        ax.plot(W, X, color=col, linewidth=2.2, label=T_lbl, zorder=4)

    # Benchmark indicator line at 99.207%
    ax.axhline(99.207, color=dk["text_muted"], linestyle=":", linewidth=1.0, alpha=0.7, zorder=2)
    ax.text(
        0.08, 95.5, r"Benchmark Limit: $99.207\%$",
        fontsize=8.5,
        color=dk["text_muted"],
        style="italic",
        zorder=5
    )

    ax.set_xlabel(r"Catalyst Bed Mass, $W$ [$\mathrm{g}$]", labelpad=6)
    ax.set_ylabel(r"$\mathrm{CO}$ Conversion, $X_{\mathrm{CO}}$ [$\%$]", labelpad=6)
    ax.set_xlim(-0.02, 3.05)
    ax.set_ylim(-2, 105)

    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))

    leg = ax.legend(
        loc="lower right",
        bbox_to_anchor=(0.95, 0.08),
        title="Reaction Temperature",
        frameon=True,
        facecolor=dk["bg_axes"],
        edgecolor=dk["grid"],
        framealpha=0.95,
        handlelength=2.2,
        handletextpad=0.6,
        labelspacing=0.45,
    )
    leg.get_title().set_fontsize(9.2)
    leg.get_title().set_color(dk["text"])

    plt.tight_layout()

    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    save_plot_duo(fig, out_dir, "06_dark_academic_presentation")
    plt.close()

if __name__ == "__main__":
    generate_plot()

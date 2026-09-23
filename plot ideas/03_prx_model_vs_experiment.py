"""
Style 3: Physical Review / Precision Science (Model vs. Experiment + Residuals)
Font: Computer Modern (CMU Serif) + TeX Math
Features:
- Two-tier stacked layout sharing X-axis with clean spacing
- Mechanistic model curve with shaded 95% confidence / parameter sensitivity band
- Discrete experimental benchmark measurements with error bars
- Sub-panel displaying model residuals (y_exp - y_model) within tolerance threshold
- Inward tick orientation on all borders (APS / IEEE / Royal Society standard)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.gridspec import GridSpec
from style_config import apply_theme, save_plot_duo

def generate_plot():
    apply_theme(font_family="CMU Serif", style="boxed_inward", font_size=10.5)

    # 1. Continuous model simulation curve
    W_model = np.linspace(0, 3.2, 250)
    X_model = 99.207 * (1.0 - np.exp(-2.55 * (W_model ** 1.28))) / (1.0 + 0.038 * np.exp(-1.75 * W_model))
    X_upper = np.clip(X_model + 3.2 * np.sqrt(W_model / 3.0) * np.exp(-0.8 * W_model), 0, 100)
    X_lower = np.clip(X_model - 3.8 * np.sqrt(W_model / 3.0) * np.exp(-0.7 * W_model), 0, 100)

    # 2. Discrete experimental benchmark points
    W_exp = np.array([0.25, 0.50, 0.75, 1.20, 1.80, 2.40, 3.00])
    X_exp_true = 99.207 * (1.0 - np.exp(-2.55 * (W_exp ** 1.28))) / (1.0 + 0.038 * np.exp(-1.75 * W_exp))
    scatter = np.array([+0.6, -1.2, +0.9, -0.7, +0.4, -0.3, +0.0])
    X_exp = np.clip(X_exp_true + scatter, 0, 99.207)
    X_err = np.array([1.4, 1.6, 1.5, 1.2, 1.0, 0.8, 0.5])

    residuals = X_exp - X_exp_true

    # 3. Figure Layout: 2-tier GridSpec with hspace=0.10
    fig = plt.figure(figsize=(5.6, 5.0))
    gs = GridSpec(nrows=2, ncols=1, height_ratios=[3.2, 1.0], hspace=0.10)

    ax_main = fig.add_subplot(gs[0])
    ax_res = fig.add_subplot(gs[1], sharex=ax_main)

    c_model = "#0F2537"       # Deep Prussian Midnight
    c_band = "#4A90E2"        # Soft Ice Blue
    c_exp = "#C92A2A"         # High-precision Ruby Carmine
    c_zero = "#718096"

    # --- MAIN PANEL ---
    ax_main.plot(
        W_model, X_model,
        color=c_model,
        linewidth=2.0,
        label=r"Reduced M4 Model ($T=350\,{}^\circ\mathrm{C}$)",
        zorder=3
    )
    ax_main.fill_between(
        W_model, X_lower, X_upper,
        color=c_band,
        alpha=0.22,
        label=r"$95\%$ Sensitivity Band",
        zorder=2
    )
    ax_main.errorbar(
        W_exp, X_exp,
        yerr=X_err,
        fmt="o",
        color=c_exp,
        ecolor=c_exp,
        elinewidth=1.2,
        capsize=3.0,
        capthick=1.1,
        markerfacecolor="#FFFFFF",
        markeredgecolor=c_exp,
        markeredgewidth=1.6,
        markersize=6.2,
        label=r"Experimental Data (GC-FID)",
        zorder=4
    )

    # Group 14 benchmark callout
    ax_main.annotate(
        r"Group-14: $99.207\%$",
        xy=(3.0, 99.207),
        xytext=(1.80, 85.0),
        arrowprops=dict(
            arrowstyle="->",
            connectionstyle="arc3,rad=-0.12",
            color=c_exp,
            lw=1.1,
        ),
        fontsize=8.8,
        fontweight="bold",
        color=c_exp,
        zorder=5
    )

    ax_main.set_ylabel(r"$\mathrm{CO}$ Conversion, $X_{\mathrm{CO}}$ [$\%$]", labelpad=6)
    ax_main.set_xlim(-0.05, 3.25)
    ax_main.set_ylim(-3, 106)
    ax_main.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax_main.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax_main.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax_main.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    plt.setp(ax_main.get_xticklabels(), visible=False)

    ax_main.legend(
        loc="lower right",
        bbox_to_anchor=(0.96, 0.08),
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#D0D0D0",
        framealpha=0.94,
        handlelength=2.0,
        handletextpad=0.6,
        labelspacing=0.45,
    )

    # Panel tag 'a'
    ax_main.text(
        0.03, 0.94, "a",
        transform=ax_main.transAxes,
        fontsize=13,
        fontweight="bold",
        va="top",
        ha="left",
    )

    # --- RESIDUAL PANEL ---
    ax_res.axhspan(-1.5, 1.5, color="#E8F5E9", alpha=0.75, zorder=1)
    ax_res.axhline(0, color=c_zero, linestyle="--", linewidth=0.85, zorder=2)

    ax_res.errorbar(
        W_exp, residuals,
        yerr=X_err,
        fmt="s",
        color=c_exp,
        ecolor=c_exp,
        elinewidth=1.0,
        capsize=2.5,
        capthick=0.9,
        markerfacecolor=c_exp,
        markeredgecolor=c_exp,
        markersize=4.8,
        zorder=4
    )

    ax_res.set_xlabel(r"Catalyst Mass, $W$ [$\mathrm{g}$]", labelpad=6)
    ax_res.set_ylabel(r"$\Delta X$ [$\%$]", labelpad=6)
    ax_res.set_ylim(-3.2, 3.2)
    ax_res.yaxis.set_major_locator(ticker.MultipleLocator(2))
    ax_res.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))

    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    save_plot_duo(fig, out_dir, "03_prx_model_vs_experiment")
    plt.close()

if __name__ == "__main__":
    generate_plot()

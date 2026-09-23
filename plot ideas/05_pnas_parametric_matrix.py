"""
Style 5: Science / PNAS 2x2 Parametric Sensitivity Matrix (Small Multiples)
Font: Source Serif 4 + Computer Modern Math
Features:
- 2x2 multi-panel layout with shared outer axis labels
- High-density information presentation for sensitivity studies
- Panel indicators (a, b, c, d) in bold serif
- Cohesive chromatic gradient illustrating systematic parameter sweeps
- Minimalist open borders with precise sub-tick registration
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from style_config import apply_theme, save_plot_duo

def generate_plot():
    apply_theme(font_family="Source Serif 4", style="clean_open", font_size=10.0)

    W = np.linspace(0, 3.0, 180)
    grad_colors = ["#1B365D", "#008080", "#D9822B", "#C84630"]

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(7.2, 5.8), sharex=True, sharey=True)
    ((ax1, ax2), (ax3, ax4)) = axes

    # --- PANEL A: Effect of Inlet Temperature ---
    T_labels = [r"$300\,{}^\circ\mathrm{C}$", r"$325\,{}^\circ\mathrm{C}$", r"$350\,{}^\circ\mathrm{C}$", r"$375\,{}^\circ\mathrm{C}$"]
    T_rates  = [1.1, 1.8, 2.7, 4.2]
    for lbl, k, col in zip(T_labels, T_rates, grad_colors):
        X = 99.5 * (1.0 - np.exp(-k * (W ** 1.3))) / (1.0 + 0.05 * np.exp(-k * W))
        ax1.plot(W, X, label=lbl, color=col, linewidth=1.9)
    ax1.set_title(r"Inlet Temperature, $T_{\mathrm{in}}$", fontsize=9.8, pad=5)
    ax1.legend(loc="lower right", frameon=False, fontsize=8.2, handlelength=1.8)
    ax1.text(-0.16, 1.06, "a", transform=ax1.transAxes, fontsize=12, fontweight="bold", va="top")

    # --- PANEL B: Effect of Feed Ratio (H2/CO) ---
    R_labels = [r"$\mathrm{H_2/CO} = 2.5$", r"$\mathrm{H_2/CO} = 3.0$", r"$\mathrm{H_2/CO} = 3.5$", r"$\mathrm{H_2/CO} = 4.0$"]
    R_max    = [88.0, 97.5, 99.2, 99.8]
    R_rates  = [2.0, 2.5, 2.8, 3.0]
    for lbl, m, k, col in zip(R_labels, R_max, R_rates, grad_colors):
        X = m * (1.0 - np.exp(-k * (W ** 1.25))) / (1.0 + 0.04 * np.exp(-1.5 * W))
        ax2.plot(W, X, label=lbl, color=col, linewidth=1.9)
    ax2.set_title(r"Feed Ratio, $\mathrm{H}_2 / \mathrm{CO}$", fontsize=9.8, pad=5)
    ax2.legend(loc="lower right", frameon=False, fontsize=8.2, handlelength=1.8)
    ax2.text(-0.10, 1.06, "b", transform=ax2.transAxes, fontsize=12, fontweight="bold", va="top")

    # --- PANEL C: Effect of System Pressure ---
    P_labels = [r"$1.0\,\mathrm{bar}$", r"$3.0\,\mathrm{bar}$", r"$7.0\,\mathrm{bar}$", r"$15.0\,\mathrm{bar}$"]
    P_rates  = [1.6, 2.4, 3.4, 4.8]
    for lbl, k, col in zip(P_labels, P_rates, grad_colors):
        X = 99.4 * (1.0 - np.exp(-k * (W ** 1.22))) / (1.0 + 0.03 * np.exp(-k * W))
        ax3.plot(W, X, label=lbl, color=col, linewidth=1.9)
    ax3.set_title(r"Total Pressure, $P$", fontsize=9.8, pad=5)
    ax3.legend(loc="lower right", frameon=False, fontsize=8.2, handlelength=1.8)
    ax3.text(-0.16, 1.06, "c", transform=ax3.transAxes, fontsize=12, fontweight="bold", va="top")

    # --- PANEL D: Effect of Catalyst Pellet Diameter ---
    D_labels = [r"$d_p = 1.0\,\mathrm{mm}$", r"$d_p = 1.5\,\mathrm{mm}$", r"$d_p = 2.0\,\mathrm{mm}$", r"$d_p = 3.0\,\mathrm{mm}$"]
    D_rates  = [3.2, 2.6, 2.0, 1.3]
    for lbl, k, col in zip(D_labels, D_rates, grad_colors):
        X = 99.2 * (1.0 - np.exp(-k * (W ** 1.28))) / (1.0 + 0.04 * np.exp(-k * W))
        ax4.plot(W, X, label=lbl, color=col, linewidth=1.9)
    ax4.set_title(r"Pellet Diameter, $d_p$", fontsize=9.8, pad=5)
    ax4.legend(loc="lower right", frameon=False, fontsize=8.2, handlelength=1.8)
    ax4.text(-0.10, 1.06, "d", transform=ax4.transAxes, fontsize=12, fontweight="bold", va="top")

    # Shared axis limits and ticks
    for ax in (ax1, ax2, ax3, ax4):
        ax.set_xlim(-0.05, 3.05)
        ax.set_ylim(-2, 105)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(1.0))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.25))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(25))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))

    # Clean non-overlapping outer label positioning
    fig.text(0.54, 0.025, r"Catalyst Mass, $W$ [$\mathrm{g}$]", ha="center", fontsize=11.0)
    fig.text(0.025, 0.52, r"$\mathrm{CO}$ Conversion, $X_{\mathrm{CO}}$ [$\%$]", va="center", rotation="vertical", fontsize=11.0)

    plt.subplots_adjust(left=0.12, bottom=0.11, right=0.97, top=0.92, wspace=0.15, hspace=0.28)

    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    save_plot_duo(fig, out_dir, "05_pnas_parametric_matrix")
    plt.close()

if __name__ == "__main__":
    generate_plot()

"""
Design 3 Scientific Plotting Module (Physical Review / Precision Science Style).

Features:
- Typography: Computer Modern (CMU Serif) + Computer Modern TeX Math (mathtext.fontset='cm').
- Frame: Full enclosed box with inward ticks on all four borders.
- Ticks: Major and minor ticks enabled with inward orientation (xtick.direction='in', ytick.direction='in').
- Palettes: High-precision physical review colors (Prussian Midnight Blue, Ruby Carmine, Cobalt Navy, Ice Blue, Sage Tolerance Band).
- Resolution: Publication-grade 300 DPI export.
"""

from __future__ import annotations

import glob
import logging
import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Suppress noisy font lookup logs for custom weights
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# ==============================================================================
# FONT DISCOVERY & REGISTRATION
# ==============================================================================
def register_publication_fonts() -> None:
    """Register local system fonts including CMU Serif if available."""
    import matplotlib.font_manager as fm

    search_dirs = []
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        search_dirs.append(os.path.join(local_appdata, "Microsoft", "Windows", "Fonts"))
    search_dirs.append("C:\\Windows\\Fonts")

    for d in search_dirs:
        if os.path.exists(d):
            for ext in ("*.ttf", "*.otf"):
                for f in glob.glob(os.path.join(d, ext)):
                    try:
                        fm.fontManager.addfont(f)
                    except Exception:
                        pass


register_publication_fonts()

# ==============================================================================
# DESIGN 3 COLOR PALETTE & STYLES
# ==============================================================================
COLOR_MODEL = "#0F2537"       # Deep Prussian Midnight Blue (Model curve)
COLOR_BAND = "#4A90E2"        # Soft Ice Blue (95% sensitivity / confidence band)
COLOR_EXP = "#C92A2A"         # High-precision Ruby Carmine (Experimental points & error bars)
COLOR_TOLERANCE = "#E8F5E9"   # Soft Sage Green (Residual tolerance band)
COLOR_TEMP = "#B82601"        # Crimson Ruby (Temperature profiles)
COLOR_PRESS = "#0A2540"       # Deep Cobalt Navy (Pressure profiles)
COLOR_GRID = "#EAEAEA"
COLOR_ZERO = "#718096"

SPECIES_PALETTE = {
    "H2":  {"color": "#0077BB", "style": "-",              "width": 2.0, "label": r"$\mathrm{H}_2$"},
    "CO":  {"color": "#CC3311", "style": "--",             "width": 2.0, "label": r"$\mathrm{CO}$"},
    "CH4": {"color": "#009988", "style": "-.",             "width": 2.0, "label": r"$\mathrm{CH}_4$"},
    "H2O": {"color": "#EE7733", "style": ":",              "width": 2.2, "label": r"$\mathrm{H}_2\mathrm{O}$"},
    "N2":  {"color": "#5A6B7C", "style": (0, (5, 2, 1, 2)), "width": 1.8, "label": r"$\mathrm{N}_2$"},
    "CO2": {"color": "#EE3377", "style": "-",              "width": 1.7, "label": r"$\mathrm{CO}_2$"},
}


def apply_design3_style(font_size: float = 10.5) -> None:
    """Apply Design 3 rcParams: CMU Serif, boxed inward ticks, 300 DPI."""
    plt.rcdefaults()
    register_publication_fonts()

    rc = {
        # Typography: CMU Serif with serif fallback
        "font.family": "serif",
        "font.serif": ["CMU Serif", "Source Serif 4", "Times New Roman", "DejaVu Serif"],
        "font.weight": 500,  # CMU Serif regular weight in Windows
        "font.size": font_size,
        "axes.titlesize": font_size * 1.12,
        "axes.titleweight": 500,
        "axes.labelsize": font_size * 1.05,
        "axes.labelweight": 500,
        "xtick.labelsize": font_size * 0.92,
        "ytick.labelsize": font_size * 0.92,
        "legend.fontsize": font_size * 0.88,
        "legend.title_fontsize": font_size * 0.90,

        # TeX Math & ASCII minus sign
        "mathtext.fontset": "cm",
        "axes.unicode_minus": False,

        # Enclosed box with inward ticks on all 4 borders
        "axes.spines.top": True,
        "axes.spines.right": True,
        "axes.spines.left": True,
        "axes.spines.bottom": True,
        "axes.edgecolor": "#111111",
        "axes.linewidth": 1.0,

        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.major.size": 4.8,
        "ytick.major.size": 4.8,
        "xtick.minor.size": 2.8,
        "ytick.minor.size": 2.8,
        "xtick.major.width": 0.9,
        "ytick.major.width": 0.9,
        "xtick.minor.width": 0.65,
        "ytick.minor.width": 0.65,

        # Lines and markers
        "lines.linewidth": 1.85,
        "lines.markersize": 6.0,
        "lines.markeredgewidth": 1.2,

        # Legend
        "legend.frameon": True,
        "legend.framealpha": 0.94,
        "legend.edgecolor": "#D0D0D0",
        "legend.fancybox": False,

        # Output resolution
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
    plt.rcParams.update(rc)


def save_figure(fig_or_plt: Any, path: Path | str, dpi: int = 300, tight: bool = True) -> None:
    """Save figure cleanly and close it."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(fig_or_plt, "savefig"):
        fig = fig_or_plt
    else:
        fig = plt.gcf()
    if tight:
        try:
            fig.tight_layout()
        except Exception:
            pass
    fig.savefig(out_path, dpi=dpi)
    if out_path.suffix.lower() == ".png":
        svg_path = out_path.with_suffix(".svg")
        fig.savefig(svg_path)
    plt.close(fig)

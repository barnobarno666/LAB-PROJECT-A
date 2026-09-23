"""
Scientific Plotting Configuration & Theme Presets
Designed for Chemical Engineering & Physical Science Publications.
Supports: Computer Modern (CMU Serif) & Source Serif 4 with TeX math.
"""

import os
import glob
import logging
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Silence noisy font fallback logging for custom weights
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# ==============================================================================
# FONT REGISTRATION
# ==============================================================================
def register_system_fonts():
    """Register user-installed fonts (CMU Serif, Source Serif 4, etc.) into matplotlib."""
    font_paths = []
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        font_paths.append(os.path.join(local_appdata, "Microsoft", "Windows", "Fonts"))
    font_paths.append("C:\\Windows\\Fonts")

    for p in font_paths:
        if os.path.exists(p):
            for ext in ("*.ttf", "*.otf"):
                for f in glob.glob(os.path.join(p, ext)):
                    try:
                        fm.fontManager.addfont(f)
                    except Exception:
                        pass

register_system_fonts()

# ==============================================================================
# CURATED COLOR PALETTES
# ==============================================================================
PALETTES = {
    "nature": {
        "primary": "#1A365D",     # Deep Prussian Navy
        "accent": "#C84630",      # Cadmium Vermilion
        "teal": "#1B7873",        # Nordic Spruce / Deep Teal
        "amber": "#D9822B",       # Warm Amber Ochre
        "purple": "#6B4C72",      # Royal Amethyst
        "slate": "#5C6F84",       # Neutral Slate
        "charcoal": "#212529",    # Near-black body text
        "grid": "#E8ECEF",        # Very faint grid
    },
    "acs": {
        "navy": "#0A2540",        # Deep Cobalt Navy (high contrast)
        "ruby": "#B82601",        # Crimson Ruby
        "gold": "#D9AB55",        # Burnished Gold
        "forest": "#1D6A42",      # Deep Pine
        "violet": "#58355E",      # Royal Violet
        "tint_bg": "#FBFBFB",     # Off-white background
        "zone_band": "#F7F1E8",   # Warm tint for reaction zone
    },
    "tol_vibrant": [
        "#0077BB",  # Blue
        "#CC3311",  # Red / Vermilion
        "#009988",  # Teal
        "#EE7733",  # Orange
        "#33BBEE",  # Cyan
        "#EE3377",  # Magenta
        "#BBBBBB",  # Grey
    ],
    "dark_academic": {
        "bg_fig": "#0E1117",      # Deep Obsidian Canvas
        "bg_axes": "#161B22",     # Dark Slate Plot Panel
        "text": "#F0F6FC",        # High-clarity Platinum text
        "text_muted": "#8B949E",  # Muted silver
        "grid": "#21262D",        # Subtle dark grid
        "cyan": "#00E5FF",        # Luminous Electric Cyan
        "coral": "#FF5376",       # Luminous Hot Coral
        "amber": "#FFB703",       # Luminous Cyber Amber
        "mint": "#06D6A0",        # Luminous Mint Emerald
    }
}

# ==============================================================================
# RC-PARAMS APPLICATION
# ==============================================================================
def apply_theme(font_family="Source Serif 4", style="clean_open", font_size=10.5):
    """
    Apply a publication-grade matplotlib configuration.
    """
    plt.rcdefaults()
    register_system_fonts()

    # Determine weight & minus sign configuration
    is_cmu = "CMU" in font_family
    weight = 500 if is_cmu else "normal"

    rc = {
        # Typography
        "font.family": "serif",
        "font.serif": [font_family, "CMU Serif", "Source Serif 4", "Times New Roman", "DejaVu Serif"],
        "font.weight": weight,
        "font.size": font_size,
        "axes.titlesize": font_size * 1.12,
        "axes.titleweight": weight,
        "axes.labelsize": font_size * 1.05,
        "axes.labelweight": weight,
        "xtick.labelsize": font_size * 0.92,
        "ytick.labelsize": font_size * 0.92,
        "legend.fontsize": font_size * 0.88,
        "legend.title_fontsize": font_size * 0.90,

        # Math text rendering
        "mathtext.fontset": "cm",
        # Fix missing glyph 8722 in CMU Serif by using standard ASCII minus:
        "axes.unicode_minus": False,

        # Lines and markers
        "lines.linewidth": 1.85,
        "lines.markersize": 6.0,
        "lines.markeredgewidth": 1.2,

        # Figure export
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }

    if style == "clean_open":
        rc.update({
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
            "axes.edgecolor": "#2B2B2B",
            "axes.linewidth": 0.9,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 4.5,
            "ytick.major.size": 4.5,
            "xtick.minor.size": 2.5,
            "ytick.minor.size": 2.5,
            "xtick.major.width": 0.85,
            "ytick.major.width": 0.85,
            "xtick.minor.width": 0.65,
            "ytick.minor.width": 0.65,
            "axes.grid": False,
            "legend.frameon": False,
        })
    elif style == "boxed_inward":
        rc.update({
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
            "legend.frameon": True,
            "legend.framealpha": 0.94,
            "legend.edgecolor": "#C0C0C0",
            "legend.fancybox": False,
        })
    elif style == "dark_mode":
        dk = PALETTES["dark_academic"]
        rc.update({
            "figure.facecolor": dk["bg_fig"],
            "axes.facecolor": dk["bg_axes"],
            "savefig.facecolor": dk["bg_fig"],
            "text.color": dk["text"],
            "axes.labelcolor": dk["text"],
            "axes.edgecolor": dk["text_muted"],
            "axes.linewidth": 1.0,
            "xtick.color": dk["text_muted"],
            "ytick.color": dk["text_muted"],
            "xtick.labelcolor": dk["text"],
            "ytick.labelcolor": dk["text"],
            "grid.color": dk["grid"],
            "grid.linestyle": "--",
            "grid.linewidth": 0.7,
            "axes.grid": True,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "legend.facecolor": dk["bg_axes"],
            "legend.edgecolor": dk["grid"],
            "legend.labelcolor": dk["text"],
            "legend.framealpha": 0.95,
        })

    plt.rcParams.update(rc)

def save_plot_duo(fig, output_dir, basename):
    """Save both 300 DPI PNG and vector SVG into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, f"{basename}.png")
    svg_path = os.path.join(output_dir, f"{basename}.svg")
    fig.savefig(png_path, dpi=300)
    fig.savefig(svg_path)
    print(f"Saved: {png_path} and {svg_path}")

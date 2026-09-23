"""
Master Execution Script: Generate All 6 Scientific Plot Ideas & Overview Gallery
Compiles high-resolution PNG (300 DPI) and vector SVG formats into plot ideas/outputs/.
Also builds '00_design_overview_gallery.png' presenting all 6 styles side-by-side.
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

sys.path.insert(0, os.path.dirname(__file__))

import importlib
import style_config

scripts = [
    ("01_nature_minimalist", "01. Nature / Science Editorial Minimalist\n(Source Serif 4, L-Frame, Rate Inset)"),
    ("02_acs_chemical_dual_axis", "02. ACS / AIChE Dual Y-Axis Classic\n(CMU Serif, Enclosed Box, Hot-Spot Band)"),
    ("03_prx_model_vs_experiment", "03. Physical Review Precision Model vs. Exp\n(CMU Serif, Residual Subplot, 95% Band)"),
    ("04_cej_multispecies_profiles", "04. CEJ Multi-Species Concentration Profiles\n(Source Serif 4, Paul Tol CVD-Safe Palette)"),
    ("05_pnas_parametric_matrix", "05. PNAS / Science 2x2 Small Multiples\n(Source Serif 4, Parametric Gradient Matrix)"),
    ("06_dark_academic_presentation", "06. Dark Academic / OLED Presentation\n(CMU Serif, Luminous Palette, Slate Canvas)"),
]

def run_all():
    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(out_dir, exist_ok=True)

    print("Generating all 6 publication styles...")
    for mod_name, title in scripts:
        print(f"-> Generating {mod_name}...")
        # Force reload to ensure code updates take effect
        if mod_name in sys.modules:
            mod = importlib.reload(sys.modules[mod_name])
        else:
            mod = importlib.import_module(mod_name)
        mod.generate_plot()

    print("\nAssembling Unified Overview Gallery Poster (00_design_overview_gallery.png)...")
    build_overview_gallery(out_dir)
    print("All tasks completed successfully!")

def build_overview_gallery(out_dir):
    style_config.register_system_fonts()
    plt.rcdefaults()
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Source Serif 4", "CMU Serif", "DejaVu Serif"]

    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(19, 13.5), dpi=250)
    fig.patch.set_facecolor("#F8F9FA")

    fig.suptitle(
        "Scientific Publication Plotting Designs — Typography & Layout Gallery\n"
        "Featuring Computer Modern (CMU Serif) & Source Serif 4 with LaTeX Math",
        fontsize=16,
        fontweight="bold",
        y=0.985,
        color="#1A202C"
    )

    for idx, (mod_name, title) in enumerate(scripts):
        row = idx // 3
        col = idx % 3
        ax = axes[row, col]

        img_path = os.path.join(out_dir, f"{mod_name}.png")
        if os.path.exists(img_path):
            img = mpimg.imread(img_path)
            ax.imshow(img)
            ax.set_title(title, fontsize=11, fontweight="bold", pad=12, color="#2D3748")
        ax.axis("off")

    plt.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02, wspace=0.12, hspace=0.22)
    gallery_path = os.path.join(out_dir, "00_design_overview_gallery.png")
    fig.savefig(gallery_path, dpi=250)
    plt.close()
    print(f"Overview gallery saved to: {gallery_path}")

if __name__ == "__main__":
    run_all()

# Scientific Publication Plot Design Ideas

This folder contains a curated suite of **6 journal-grade scientific plot templates** specifically tailored for chemical engineering, reactor kinetics, and physical sciences. 

All styles use **publishable LaTeX-grade serif fonts** natively installed on your system:
- **`Source Serif 4`**: Adobe's modern, highly legible editorial serif (featured in *Nature*, *Science*, *Cell*).
- **`CMU Serif` (Computer Modern Unicode Serif)**: The classic TeX / LaTeX typography standard (featured in *ACS Catalysis*, *AIChE J.*, *Physical Review*).
- **Computer Modern Math (`mathtext.fontset = 'cm'`)**: Ensures all mathematical expressions, subscripts ($\mathrm{CO}, \mathrm{CH}_4$), fractions, and units render with true LaTeX typesetting quality without requiring an external TeX installation.

---

## Visual Gallery Overview

All 6 styles have been generated as **300 DPI high-resolution PNGs** and **lossless vector SVGs** in the [`outputs/`](outputs/) directory.

| # | Style Name | Font | Primary Aesthetic | Best For |
|---|---|---|---|---|
| **01** | **[Nature / Science Editorial Minimalist](outputs/01_nature_minimalist.png)** | `Source Serif 4` | Open L-frame, no top/right spines, inset rate zoom | Main article executive summary, multi-rate comparisons |
| **02** | **[ACS / AIChE Chemical Engineering Dual Y-Axis](outputs/02_acs_chemical_dual_axis.png)** | `CMU Serif` | Enclosed box, inward ticks, shaded reaction hot-zone, dual axes | Axial reactor profiles ($T$ and $X_{\mathrm{CO}}$ along bed) |
| **03** | **[Physical Review Precision Model vs. Experiment](outputs/03_prx_model_vs_experiment.png)** | `CMU Serif` | Two-tier stacked layout, 95% sensitivity band, error bars, residual sub-panel | Mechanistic model validation against experimental benchmarks |
| **04** | **[CEJ Multi-Species Concentration Profiles](outputs/04_cej_multispecies_profiles.png)** | `Source Serif 4` | Paul Tol CVD-safe palette, distinct line dashes, direct line labels | Multi-component gas phase mole fractions ($y_{\mathrm{H_2}}, y_{\mathrm{CO}}, \dots$) |
| **05** | **[PNAS / Science 2x2 Parametric Matrix](outputs/05_pnas_parametric_matrix.png)** | `Source Serif 4` | 4-panel small multiples, shared outer labels, chromatic gradient | Multi-parameter sensitivity sweeps ($T_{\mathrm{in}}$, ratio, $P, d_p$) |
| **06** | **[Dark Academic / OLED Presentation Grade](outputs/06_dark_academic_presentation.png)** | `CMU Serif` | Obsidian slate canvas (`#0E1117`), luminous neon curves, subtle dark grid | Conference keynote slides, thesis defense, dark mode papers |

---

## Detailed Style Descriptions

### Style 1: Nature / Science Editorial Minimalist
- **Script**: [`01_nature_minimalist.py`](01_nature_minimalist.py)
- **Outputs**: [`01_nature_minimalist.png`](outputs/01_nature_minimalist.png), [`01_nature_minimalist.svg`](outputs/01_nature_minimalist.svg)
- **Palette**: Deep Prussian Navy (`#1A365D`), Cadmium Vermilion (`#C84630`), Nordic Spruce Teal (`#1B7873`), Warm Honey Amber (`#D9822B`).
- **Design Features**:
  - Removes visual clutter with an open L-frame (top and right borders omitted).
  - Prominent panel badge (**a** in bold serif).
  - Includes an inset secondary plot ($r_{\mathrm{CH_4}}$ vs $z/L$) with a solid background box.

### Style 2: ACS / AIChE Chemical Engineering Classic (Dual Y-Axis)
- **Script**: [`02_acs_chemical_dual_axis.py`](02_acs_chemical_dual_axis.py)
- **Outputs**: [`02_acs_chemical_dual_axis.png`](outputs/02_acs_chemical_dual_axis.png), [`02_acs_chemical_dual_axis.svg`](outputs/02_acs_chemical_dual_axis.svg)
- **Palette**: Deep Cobalt Navy (`#0A2540`), Crimson Ruby (`#B82601`), Warm Tint Zone (`#F7F1E8`).
- **Design Features**:
  - Full boxed enclosure with inward ticks on all 4 borders.
  - Left axis for Bed Temperature $T$ and right axis for Conversion $X_{\mathrm{CO}}$.
  - Shaded "Kinetic Hot-Spot Zone" band highlighting the exothermic reaction zone ($W < 0.85\,\mathrm{g}$).
  - Vector arrow annotation calling out $T_{\mathrm{max}} = 388.4\,{}^\circ\mathrm{C}$.

### Style 3: Physical Review Precision (Model vs. Experiment with Residuals)
- **Script**: [`03_prx_model_vs_experiment.py`](03_prx_model_vs_experiment.py)
- **Outputs**: [`03_prx_model_vs_experiment.png`](outputs/03_prx_model_vs_experiment.png), [`03_prx_model_vs_experiment.svg`](outputs/03_prx_model_vs_experiment.svg)
- **Palette**: Midnight Blue (`#0F2537`), Soft Ice Blue (`#4A90E2`), Ruby Carmine (`#C92A2A`), Sage Tolerance Zone (`#E8F5E9`).
- **Design Features**:
  - Main panel displays the continuous model prediction, shaded $95\%$ parameter sensitivity band, and discrete experimental data points with error bars.
  - Highlights the Group-14 verification benchmark point ($99.207\%$ at $3.0\,\mathrm{g}$).
  - Bottom sub-panel plots residuals ($\Delta X = X_{\mathrm{exp}} - X_{\mathrm{model}}$) inside a green $\pm 1.5\%$ experimental error corridor.

### Style 4: Chemical Engineering Journal Multi-Species Profiles
- **Script**: [`04_cej_multispecies_profiles.py`](04_cej_multispecies_profiles.py)
- **Outputs**: [`04_cej_multispecies_profiles.png`](outputs/04_cej_multispecies_profiles.png), [`04_cej_multispecies_profiles.svg`](outputs/04_cej_multispecies_profiles.svg)
- **Palette**: Paul Tol CVD-safe (Blue `#0077BB`, Vermilion `#CC3311`, Teal `#009988`, Amber `#EE7733`, Magenta `#EE3377`, Grey `#5A6B7C`).
- **Design Features**:
  - Every curve has a unique line style (solid, dashed, dash-dot, dotted) so it remains 100% legible in greyscale/black-and-white printing.
  - Direct right-side chemical formula callouts ($\mathrm{H_2}, \mathrm{CO}, \mathrm{CH_4}, \mathrm{H_2O}, \mathrm{N_2}, \mathrm{CO_2}$).
  - Delicate horizontal grid lines for reading precise composition values.

### Style 5: Science / PNAS 2x2 Parametric Sensitivity Matrix
- **Script**: [`05_pnas_parametric_matrix.py`](05_pnas_parametric_matrix.py)
- **Outputs**: [`05_pnas_parametric_matrix.png`](outputs/05_pnas_parametric_matrix.png), [`05_pnas_parametric_matrix.svg`](outputs/05_pnas_parametric_matrix.svg)
- **Palette**: Sequential chromatic gradient (`#1B365D` $\to$ `#008080` $\to$ `#D9822B` $\to$ `#C84630`).
- **Design Features**:
  - Compact 2x2 multi-panel layout with shared outer axis labels.
  - Evaluates 4 parameters: Inlet Temperature $T_{\mathrm{in}}$, Feed Ratio $\mathrm{H_2/CO}$, Total Pressure $P$, and Catalyst Pellet Diameter $d_p$.
  - Clean individual panel tags (**a**, **b**, **c**, **d**).

### Style 6: Dark Academic / OLED Presentation Grade
- **Script**: [`06_dark_academic_presentation.py`](06_dark_academic_presentation.py)
- **Outputs**: [`06_dark_academic_presentation.png`](outputs/06_dark_academic_presentation.png), [`06_dark_academic_presentation.svg`](outputs/06_dark_academic_presentation.svg)
- **Palette**: Deep Obsidian Canvas (`#0E1117`), Dark Slate Panel (`#161B22`), Luminous Cyan (`#00E5FF`), Mint (`#06D6A0`), Cyber Amber (`#FFB703`), Coral (`#FF5376`).
- **Design Features**:
  - High-contrast glowing curves with subtle ambient halo.
  - Platinum white text (`#F0F6FC`) and muted silver ticks.
  - Designed for conference slides, Keynote/PowerPoint presentations, and defense talks.

---

## How to Run & Regenerate

To regenerate all figures and the master overview poster with one command:

```powershell
.\.venv\Scripts\python.exe "plot ideas\generate_all_plots.py"
```

To run an individual style script:

```powershell
.\.venv\Scripts\python.exe "plot ideas\01_nature_minimalist.py"
.\.venv\Scripts\python.exe "plot ideas\02_acs_chemical_dual_axis.py"
.\.venv\Scripts\python.exe "plot ideas\03_prx_model_vs_experiment.py"
.\.venv\Scripts\python.exe "plot ideas\04_cej_multispecies_profiles.py"
.\.venv\Scripts\python.exe "plot ideas\05_pnas_parametric_matrix.py"
.\.venv\Scripts\python.exe "plot ideas\06_dark_academic_presentation.py"
```

---

## Reusing in the Main Reactor Codebase

Each script imports from [`style_config.py`](style_config.py). To adopt your favorite style in your actual simulation pipeline:

```python
from style_config import apply_theme, PALETTES, save_plot_duo

# 1. Apply your chosen theme and font
apply_theme(font_family="Source Serif 4", style="clean_open")
# or: apply_theme(font_family="CMU Serif", style="boxed_inward")

# 2. Plot your actual simulation data from results/ or model solver
fig, ax = plt.subplots(figsize=(5.5, 4.0))
ax.plot(bed_profile["mass_kg"] * 1e3, bed_profile["X_CO"] * 100.0, color=PALETTES["nature"]["primary"])

# 3. Save as publication-ready PNG + vector SVG
save_plot_duo(fig, "results/final_figures", "co_conversion_profile")
```

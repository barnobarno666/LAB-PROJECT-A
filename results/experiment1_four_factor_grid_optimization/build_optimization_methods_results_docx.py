"""Build the methods and results paper from the saved four-factor M4 grid."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


HERE = Path(__file__).resolve().parent
SUMMARY = json.loads((HERE / "optimization_summary.json").read_text(encoding="utf-8"))
BEST = SUMMARY["best_grid_case"]
REFERENCE = SUMMARY["reference_case"]
FACTORS = (
    "h2_co_molar_ratio",
    "inlet_temperature_c",
    "inlet_pressure_bar_abs",
    "catalyst_space_time_kg_s_mol_co",
)
with (HERE / "four_factor_grid_search.csv").open(newline="", encoding="utf-8") as source:
    GRID_ROWS = list(csv.DictReader(source))
OUTPUT = HERE / "optimization_methods_results_detailed.docx"


def slice_row(factor: str, value: float) -> dict[str, str]:
    matches = [
        row
        for row in GRID_ROWS
        if row["status"] == "completed"
        and abs(float(row[factor]) - value) < 1e-8
        and all(abs(float(row[key]) - float(BEST[key])) < 1e-8 for key in FACTORS if key != factor)
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one saved grid row for {factor}={value}; found {len(matches)}")
    return matches[0]


def slice_conversion(factor: str, value: float) -> float:
    return float(slice_row(factor, value)["outlet_co_conversion_pct"])


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_borders(cell) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), "D9D9D9")


def set_cell_margin(cell, top=75, start=105, bottom=75, end=105) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    mar = tc_pr.first_child_found_in("w:tcMar")
    if mar is None:
        mar = OxmlElement("w:tcMar")
        tc_pr.append(mar)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def add_field(paragraph, instruction: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for item in (begin, instr, separate, text, end):
        run._r.append(item)


def add_math_run(parent, text: str) -> None:
    run = OxmlElement("m:r")
    node = OxmlElement("m:t")
    node.text = text
    run.append(node)
    parent.append(run)


def add_subscript(parent, base: str, sub: str) -> None:
    node = OxmlElement("m:sSub")
    main = OxmlElement("m:e")
    add_math_run(main, base)
    lower = OxmlElement("m:sub")
    add_math_run(lower, sub)
    node.extend((main, lower))
    parent.append(node)


def add_conversion_equation(doc: Document) -> None:
    paragraph = doc.add_paragraph(style="Equation")
    math_para = OxmlElement("m:oMathPara")
    math = OxmlElement("m:oMath")
    add_subscript(math, "X", "CO,out")
    add_math_run(math, " = 100(1 − ")
    fraction = OxmlElement("m:f")
    numerator = OxmlElement("m:num")
    denominator = OxmlElement("m:den")
    add_subscript(numerator, "F", "CO,out")
    add_subscript(denominator, "F", "CO,in")
    fraction.extend((numerator, denominator))
    math.append(fraction)
    add_math_run(math, ") %")
    math_para.append(math)
    paragraph._p.append(math_para)


def add_space_time_equation(doc: Document) -> None:
    paragraph = doc.add_paragraph(style="Equation")
    math_para = OxmlElement("m:oMathPara")
    math = OxmlElement("m:oMath")
    add_subscript(math, "τ", "CO")
    add_math_run(math, " = ")
    fraction = OxmlElement("m:f")
    numerator = OxmlElement("m:num")
    denominator = OxmlElement("m:den")
    add_subscript(numerator, "W", "cat")
    add_subscript(denominator, "F", "CO,in")
    fraction.extend((numerator, denominator))
    math.append(fraction)
    math_para.append(math)
    paragraph._p.append(math_para)


def add_figure(doc: Document, filename: str, caption: str, *, new_page: bool = False) -> None:
    paragraph = doc.add_paragraph(style="Figure")
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.page_break_before = new_page
    paragraph.add_run().add_picture(str(HERE / filename), width=Inches(5.72))
    cap = doc.add_paragraph(style="Caption")
    cap.add_run(caption)


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.78)
    section.bottom_margin = Inches(0.76)
    section.left_margin = Inches(0.80)
    section.right_margin = Inches(0.80)
    section.header_distance = Inches(0.3)
    section.footer_distance = Inches(0.37)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10.3)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.line_spacing = 1.10
    normal.paragraph_format.space_after = Pt(5)

    title = styles["Title"]
    title.font.name = "Times New Roman"
    title.font.size = Pt(16.5)
    title.font.bold = True
    title.font.color.rgb = RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(8)
    title_ppr = title.element.get_or_add_pPr()
    for border in title_ppr.findall(qn("w:pBdr")):
        title_ppr.remove(border)
    title_rpr = title.element.get_or_add_rPr()
    title_fonts = title_rpr.rFonts
    if title_fonts is not None:
        for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "csTheme"):
            title_fonts.attrib.pop(qn(f"w:{attr}"), None)
        for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
            title_fonts.set(qn(f"w:{attr}"), "Times New Roman")

    for name in ("Heading 1", "Heading 2"):
        style = styles[name]
        style.font.name = "Times New Roman"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True
        style.paragraph_format.keep_with_next = True
    styles["Heading 1"].font.size = Pt(12.5)
    styles["Heading 1"].paragraph_format.space_before = Pt(12)
    styles["Heading 1"].paragraph_format.space_after = Pt(5)
    styles["Heading 2"].font.size = Pt(11)
    styles["Heading 2"].paragraph_format.space_before = Pt(9)
    styles["Heading 2"].paragraph_format.space_after = Pt(3)

    equation_style = styles.add_style("Equation", 1)
    equation_style.base_style = normal
    equation_style.paragraph_format.space_before = Pt(1)
    equation_style.paragraph_format.space_after = Pt(7)
    equation_style.paragraph_format.left_indent = Inches(0.2)

    figure_style = styles.add_style("Figure", 1)
    figure_style.base_style = normal
    figure_style.paragraph_format.space_after = Pt(2)
    figure_style.alignment = WD_ALIGN_PARAGRAPH.CENTER

    caption_style = styles["Caption"]
    caption_style.font.name = "Times New Roman"
    caption_style.font.size = Pt(9)
    caption_style.font.bold = False
    caption_style.font.color.rgb = RGBColor(0, 0, 0)
    caption_style.paragraph_format.line_spacing = 1.05
    caption_style.paragraph_format.space_before = Pt(1)
    caption_style.paragraph_format.space_after = Pt(12)
    caption_style.alignment = WD_ALIGN_PARAGRAPH.CENTER

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.style = normal
    footer.add_run("Page ")
    add_field(footer, "PAGE")
    for run in footer.runs:
        run.font.size = Pt(8)

    doc.add_paragraph("Four Factor Optimization of CO Methanation in a Fixed Bed Reactor", style="Title")
    doc.add_paragraph(
        "A 20,412-case search of the Full M4 fixed bed model selected H₂/CO = 5.0, 370 °C, "
        "15 bar absolute, and a catalyst space time of 140.4 kg catalyst·s/mol CO. Predicted outlet "
        "CO conversion was 99.999993%. The selected point lies on three grid boundaries and is a "
        "conditional model result, not a measured operating optimum."
    )

    doc.add_heading("Methodology", level=1)
    doc.add_heading("Reactor model and fixed basis", level=2)
    doc.add_paragraph(
        "The Full M4 model follows CO, H₂, CH₄, H₂O, CO₂, and N₂ through a catalyst bed. It includes "
        "CO methanation, CO₂ methanation, and the water gas shift reaction. Species molar balances "
        "are integrated against catalyst mass. At each axial position, local mole fractions and "
        "pressure determine the species partial pressures used in the rate expressions. The original "
        "M4 kinetic constants were retained; no parameter was adjusted to reproduce Experiment 1."
    )
    doc.add_paragraph(
        "Catalyst mass was held at 3.12 g. The assumed tube diameter and bed length were 25.4 mm "
        "and 304.8 mm; particle diameter was 3 mm. An assumed particle density of 1250 kg m⁻³ "
        "sets the bed voidage to 0.98384 for this catalyst charge and geometry. This unusually sparse "
        "bed is part of the numerical basis, not a measured packed bed property. Temperature was "
        "constant along the bed, while the Ergun relation supplied the axial pressure change. The "
        "inlet contained CO, H₂, and N₂, with N₂/CO fixed at 2.496875."
    )
    doc.add_heading("Factor grid and feed construction", level=2)
    doc.add_paragraph(
        "The four inputs were inlet H₂/CO ratio, temperature, absolute pressure, and catalyst space "
        "time on an inlet CO basis. Ratio, temperature, and pressure levels came from the earlier "
        "three-factor map; the 21 space times came from the earlier ratio–space-time sweep. The "
        "ratio grid includes both the recorded Experiment 1 ratio of 2.996875 and the rounded value "
        "3.0. Temperature was sampled at 250, 280, 300, 310, 340, 350, 370, 385, and 400 °C. "
        "Pressure was sampled at 1, 2, 3, 4, 5, 7, 9, 12, and 15 bar absolute. Space time ran from "
        "8.775 to 140.4 kg catalyst·s/mol CO with geometric spacing."
    )
    doc.add_paragraph("Catalyst space time was defined as")
    add_space_time_equation(doc)
    doc.add_paragraph(
        "where catalyst mass is in kilograms and inlet CO flow is in mol s⁻¹. At every grid point, "
        "the selected space time set the CO flow. H₂ flow equaled the selected H₂/CO ratio times "
        "CO flow; N₂ flow equaled 2.496875 times CO flow. Thus changing space time scaled all three "
        "feeds together, whereas changing H₂/CO changed the H₂ feed alone at a given space time. "
        "Neither CO throughput nor total inlet flow was fixed across the optimization."
    )

    doc.add_heading("Numerical search and figure construction", level=2)
    doc.add_paragraph(
        "The Cartesian product contained 12 × 9 × 9 × 21 = 20,412 model cases. Each dry-feed case "
        "used the model's near-inlet start before integration with SciPy's BDF solver. Relative "
        "tolerance was 10⁻⁶, and the absolute molar-flow tolerance was 10⁻¹⁴ mol s⁻¹. A case "
        "counted as completed only if integration reached the full 3.12 g catalyst mass without "
        "a terminal pressure, temperature, or hydrogen event. All 20,412 cases completed. The "
        "saved grid records the inlet factors, outlet conversion and methane yield, feed flows, "
        "outlet pressure, and solver status for each case."
    )
    doc.add_paragraph("The objective was outlet CO conversion on the inlet CO basis:")
    add_conversion_equation(doc)
    doc.add_paragraph(
        "Methane yield was calculated as net outlet CH₄ production divided by inlet CO flow and "
        "reported separately. The case with the largest computed conversion was selected; the "
        "objective contains no charge for hydrogen, pressure, or loss of throughput. The four "
        "figures vary one factor at a time around the selected case and use separate enlarged "
        "vertical scales. The pressure slice includes 1–4 bar points, which extrapolate the "
        "5–15 bar kinetic fit interval."
    )

    doc.add_heading("Results and discussion", level=1)
    caption = doc.add_paragraph(style="Caption")
    caption.alignment = WD_ALIGN_PARAGRAPH.LEFT
    caption.paragraph_format.keep_with_next = True
    caption.add_run("Table 1. Search ranges and best sampled model result.")

    rows = [
        ("Inlet H₂/CO ratio", "1.0–5.0 (12 levels)", f"{BEST['h2_co_molar_ratio']:.1f}"),
        ("Inlet temperature", "250–400 °C (9 levels)", f"{BEST['inlet_temperature_c']:.0f} °C"),
        ("Inlet pressure", "1–15 bar abs (9 levels)", f"{BEST['inlet_pressure_bar_abs']:.0f} bar abs"),
        ("Catalyst space time", "8.775–140.4 (21 levels)", "140.4 kg catalyst·s/mol CO"),
        ("CO / H₂ / N₂ inlet flow", "Derived from inputs", "0.080 / 0.400 / 0.19975 mol h⁻¹"),
        ("Outlet CO conversion", "Objective", f"{BEST['outlet_co_conversion_pct']:.6f}%"),
        ("Outlet CH₄ yield", "Predicted output", f"{BEST['outlet_ch4_yield_pct']:.6f}%"),
    ]
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = [Inches(2.22), Inches(2.05), Inches(2.42)]
    for cell, name, width in zip(table.rows[0].cells, ("Quantity", "Grid or role", "Best sampled value"), widths):
        cell.width = width
        cell.text = name
    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        for cell, value, width in zip(cells, values, widths):
            cell.width = width
            cell.text = value
            set_cell_shading(cell, "F4F5F6" if row_index % 2 else "FFFFFF")
    for row_index, row in enumerate(table.rows):
        for col_index, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_borders(cell)
            set_cell_margin(cell)
            if row_index == 0:
                set_cell_shading(cell, "263746")
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.07
                if col_index > 0:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(8.8)
                    if row_index == 0:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)

    doc.add_heading("Best sampled case", level=2)
    doc.add_paragraph(
        f"The highest completed-bed conversion was {BEST['outlet_co_conversion_pct']:.8f}%, with a "
        f"predicted methane yield of {BEST['outlet_ch4_yield_pct']:.8f}%. Total inlet flow was "
        "0.67975 mol h⁻¹. Temperature was an interior grid value, while ratio, pressure, and "
        "space time reached their upper sampled bounds. The grid therefore does not locate "
        "interior maxima for those three inputs. Methane yield was recorded, not optimized "
        "as a second objective."
    )
    doc.add_heading("Hydrogen ratio and temperature", level=2)
    doc.add_paragraph(
        "With temperature, pressure, and space time fixed at the selected setting, conversion rose "
        f"from {slice_conversion('h2_co_molar_ratio', 1.0):.4f}% at H₂/CO = 1.0 to "
        f"{slice_conversion('h2_co_molar_ratio', 1.4):.4f}% at 1.4 (Figure 1). At a ratio of 3.0 "
        f"it was {slice_conversion('h2_co_molar_ratio', 3.0):.4f}%, and at 5.0 it was "
        f"{BEST['outlet_co_conversion_pct']:.6f}%. Most of the change occurred at the low end of "
        "the ratio range. Further hydrogen addition had little effect after outlet CO was nearly "
        "depleted."
    )
    doc.add_paragraph(
        "Along the temperature slice, conversion was "
        f"{slice_conversion('inlet_temperature_c', 250.0):.6f}% at 250 °C and "
        f"{slice_conversion('inlet_temperature_c', 350.0):.6f}% at 350 °C (Figure 2). It reached "
        f"{BEST['outlet_co_conversion_pct']:.6f}% at the sampled 370 °C point, then fell to "
        f"{slice_conversion('inlet_temperature_c', 400.0):.6f}% at 400 °C. The difference between "
        "370 and 400 °C is about 0.000032 percentage points. Thus 370 °C is the sampled maximum, "
        "but the high-temperature peak is shallow on an absolute conversion scale."
    )
    doc.add_heading("Pressure and catalyst space time", level=2)
    doc.add_paragraph(
        "At the selected ratio, temperature, and space time, the pressure slice gave "
        f"{slice_conversion('inlet_pressure_bar_abs', 1.0):.4f}% conversion at 1 bar, "
        f"{slice_conversion('inlet_pressure_bar_abs', 5.0):.6f}% at 5 bar, and "
        f"{BEST['outlet_co_conversion_pct']:.6f}% at 15 bar (Figure 3). The 1–4 bar portion is "
        "outside the fitted pressure interval. Within 5–15 bar, the gain is about 0.000880 "
        "percentage points at this already high conversion. Pressure has no cost in the objective, "
        "and its selected value is the upper grid bound."
    )
    doc.add_paragraph(
        "The space time slice shows the associated throughput change. Conversion increased from "
        f"{slice_conversion('catalyst_space_time_kg_s_mol_co', 8.775):.4f}% at "
        "8.775 kg catalyst·s/mol CO to "
        f"{slice_conversion('catalyst_space_time_kg_s_mol_co', 35.1):.5f}% at 35.1 and "
        f"{slice_conversion('catalyst_space_time_kg_s_mol_co', 70.2):.6f}% at 70.2 (Figure 4). "
        "The 140.4 setting gave the largest conversion, but it lowered the CO inlet flow from "
        "1.28 mol h⁻¹ at the 8.775 setting to 0.080 mol h⁻¹, a sixteenfold reduction. With "
        "H₂/CO = 5.0 and the fixed N₂/CO ratio, total inlet flow likewise fell from 10.876 to "
        "0.67975 mol h⁻¹. The conversion-only objective favors the longer space time despite "
        "the much smaller feed rate."
    )
    doc.add_heading("Limits of interpretation", level=2)
    doc.add_paragraph(
        f"The saved optimization summary compares its 2 bar reference case with a source-reported "
        f"CO conversion of {REFERENCE['source_reported_co_conversion_pct']:.2f}%; the model gives "
        f"{REFERENCE['outlet_co_conversion_pct']:.2f}% at that saved point. The Experiment 1 "
        "abstract and results describe atmospheric operation, whereas an appendix states 2 bar. "
        "The saved comparison uses the appendix pressure and does not validate the model at the "
        "atmospheric-pressure reading. The reported conversion was not a kinetic fitting target."
    )
    doc.add_paragraph(
        "The assumed bed voidage and isothermal operation also constrain the physical meaning "
        "of the near-complete predicted conversion. The result is the best sampled case, not a "
        "continuous optimum. Boundary values for ratio, pressure, and space time, together with "
        "unpenalized hydrogen use and throughput, preclude an operating recommendation without "
        "additional constraints and experimental checks."
    )

    add_figure(doc, "sensitivity_h2_co_ratio.png", "Figure 1. Outlet CO conversion across the sampled H₂/CO ratios.", new_page=True)
    add_figure(doc, "sensitivity_inlet_temperature.png", "Figure 2. Outlet CO conversion across the sampled inlet temperatures.")

    add_figure(doc, "sensitivity_inlet_pressure.png", "Figure 3. Outlet CO conversion across the sampled inlet pressures.", new_page=True)
    add_figure(doc, "sensitivity_catalyst_space_time.png", "Figure 4. Outlet CO conversion across the sampled catalyst space times.")

    doc.core_properties.title = "Four Factor Optimization of CO Methanation in a Fixed Bed Reactor"
    doc.core_properties.subject = "Methodology and results from the saved Full M4 grid search"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()

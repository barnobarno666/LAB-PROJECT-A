"""Profile export and required base-case figure generation."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from .constants import SPECIES
from .reactor import SimulationResult


def _write_profiles(result: SimulationResult, output_dir: Path) -> None:
    columns = [
        "catalyst_mass_kg", "bed_length_m", "temperature_k", "pressure_bar",
        "co_conversion", "methane_yield",
    ]
    columns += [f"flow_{name}_mol_s" for name in SPECIES]
    columns += [f"concentration_{name}_mol_m3" for name in SPECIES]
    concentrations = result.concentrations_mol_m3
    with (output_dir / "profiles.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        for i in range(len(result.catalyst_mass_kg)):
            writer.writerow([
                result.catalyst_mass_kg[i], result.bed_length_m[i], result.temperature_k[i], result.pressure_pa[i] / 100_000.0,
                result.co_conversion[i], result.methane_yield[i],
                *result.molar_flows_mol_s[i], *concentrations[i],
            ])


from .plotting import (
    COLOR_MODEL,
    COLOR_PRESS,
    COLOR_TEMP,
    SPECIES_PALETTE,
    apply_design3_style,
    save_figure,
)


def _savefig(fig: plt.Figure, path: Path) -> None:
    save_figure(fig, path, dpi=300)


def _make_figures(result: SimulationResult, output_dir: Path) -> None:
    apply_design3_style(font_size=10.5)

    # 1. CO conversion vs. bed length
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    conv_pct = result.co_conversion * 100.0
    ax.plot(
        result.bed_length_m,
        conv_pct,
        color=COLOR_MODEL,
        linewidth=2.2,
        label=r"Reduced M4 Model",
        zorder=3,
    )
    ax.set_xlabel(r"Bed Length, $z$ [$\mathrm{m}$]", labelpad=6)
    ax.set_ylabel(r"$\mathrm{CO}$ Conversion, $X_{\mathrm{CO}}$ [$\%$]", labelpad=6)
    ax.set_xlim(0.0, float(result.bed_length_m[-1]))
    ax.set_ylim(-2.0, 105.0)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.legend(loc="lower right", bbox_to_anchor=(0.95, 0.08), handlelength=2.0)
    _savefig(fig, output_dir / "co_conversion_vs_bed_length.png")

    # 2. CO conversion vs. catalyst mass
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    ax.plot(
        result.catalyst_mass_kg,
        conv_pct,
        color=COLOR_MODEL,
        linewidth=2.2,
        label=r"Reduced M4 Model",
        zorder=3,
    )
    ax.set_xlabel(r"Catalyst Mass, $W$ [$\mathrm{kg}$]", labelpad=6)
    ax.set_ylabel(r"$\mathrm{CO}$ Conversion, $X_{\mathrm{CO}}$ [$\%$]", labelpad=6)
    ax.set_xlim(0.0, float(result.catalyst_mass_kg[-1]))
    ax.set_ylim(-2.0, 105.0)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.legend(loc="lower right", bbox_to_anchor=(0.95, 0.08), handlelength=2.0)
    _savefig(fig, output_dir / "co_conversion_vs_catalyst_mass.png")

    # 3. Species concentrations vs. bed length
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    for i, species in enumerate(SPECIES):
        sp_style = SPECIES_PALETTE.get(
            species,
            {"color": "#333333", "style": "-", "width": 1.8, "label": species},
        )
        ax.plot(
            result.bed_length_m,
            result.concentrations_mol_m3[:, i],
            color=sp_style["color"],
            linestyle=sp_style["style"],
            linewidth=sp_style["width"],
            label=sp_style["label"],
            zorder=3,
        )
    ax.set_xlabel(r"Bed Length, $z$ [$\mathrm{m}$]", labelpad=6)
    ax.set_ylabel(r"Gas Concentration, $C_i$ [$\mathrm{mol}\cdot\mathrm{m}^{-3}$]", labelpad=6)
    ax.set_xlim(0.0, float(result.bed_length_m[-1]))
    ax.set_ylim(bottom=0.0)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.legend(
        loc="upper right",
        ncol=2,
        handlelength=2.2,
        columnspacing=1.0,
        handletextpad=0.5,
        labelspacing=0.4,
    )
    _savefig(fig, output_dir / "species_concentrations_vs_bed_length.png")

    # 4. Temperature and pressure vs. bed length (Dual Y-Axis)
    fig, ax_temp = plt.subplots(figsize=(6.2, 4.4))
    ax_press = ax_temp.twinx()

    l_temp = ax_temp.plot(
        result.bed_length_m,
        result.temperature_k,
        color=COLOR_TEMP,
        linewidth=2.2,
        label=r"Temperature $T$ [$\mathrm{K}$]",
        zorder=3,
    )
    press_bar = result.pressure_pa / 100_000.0
    l_press = ax_press.plot(
        result.bed_length_m,
        press_bar,
        color=COLOR_PRESS,
        linewidth=2.0,
        linestyle="--",
        label=r"Pressure $P$ [$\mathrm{bar}$]",
        zorder=3,
    )

    ax_temp.set_xlabel(r"Bed Length, $z$ [$\mathrm{m}$]", labelpad=6)
    ax_temp.set_ylabel(r"Bed Temperature, $T$ [$\mathrm{K}$]", color=COLOR_TEMP, labelpad=6)
    ax_temp.tick_params(axis="y", labelcolor=COLOR_TEMP, which="both")
    ax_temp.set_xlim(0.0, float(result.bed_length_m[-1]))
    ax_temp.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax_temp.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))

    ax_press.set_ylabel(r"Pressure, $P$ [$\mathrm{bar}$]", color=COLOR_PRESS, labelpad=6)
    ax_press.tick_params(axis="y", labelcolor=COLOR_PRESS, which="both")
    ax_press.tick_params(direction="in", which="both")
    ax_press.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax_press.ticklabel_format(axis="y", style="plain", useOffset=False)

    for sp in ax_press.spines.values():
        sp.set_linewidth(1.0)

    lines = l_temp + l_press
    labels = [line.get_label() for line in lines]
    leg = ax_temp.legend(
        lines,
        labels,
        loc="center right",
        bbox_to_anchor=(0.96, 0.50),
        handlelength=2.2,
        labelspacing=0.5,
    )
    leg.set_zorder(6)
    _savefig(fig, output_dir / "temperature_and_pressure_vs_bed_length.png")


def write_outputs(result: SimulationResult, output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_profiles(result, output)
    _make_figures(result, output)
    peak_index = int(np.argmax(result.temperature_k))
    summary = {
        "reaction_mode": result.config.reaction_mode,
        "status": "completed" if result.success else "incomplete_or_failed",
        "message": result.message,
        "terminal_event": result.terminal_event,
        "solver_method": result.config.solver.method,
        "solver_function_evaluations": result.nfev,
        "configured_catalyst_mass_kg": result.config.catalyst_mass_kg,
        "reached_catalyst_mass_kg": float(result.catalyst_mass_kg[-1]),
        "outlet_co_conversion": float(result.co_conversion[-1]),
        "outlet_methane_yield": float(result.methane_yield[-1]),
        "peak_temperature_k": float(result.temperature_k[peak_index]),
        "peak_temperature_location_m": float(result.bed_length_m[peak_index]),
        "outlet_pressure_bar": float(result.pressure_pa[-1] / 100_000.0),
        "elemental_relative_residuals": result.elemental_residuals(),
        "assumption_notice": "This configuration contains assumed inputs and is not an Experiment #1 validation run."
    }
    (output / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output / "resolved_config.json").write_text(
        json.dumps(result.config.to_dict(), indent=2), encoding="utf-8"
    )

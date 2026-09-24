"""Three-model, one-bar verification for the Experiment 1 CO conversion.

This module is deliberately separate from the production M4 reactor.  It keeps
the Experiment 1 flow, temperature, catalyst-mass, isothermal, and
constant-pressure basis, then compares full M4 with two published low-pressure
literature kinetics without fitting any parameter to the reported conversion.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from scipy.integrate import solve_ivp

from .constants import ELEMENT_MATRIX, INDEX, R_J_MOL_K, SPECIES, STOICH_FULL
from .experiment_verification import (
    _model_input_data,
    audit_experiment1_data,
    compare_experiment1,
)
from .plotting import COLOR_EXP, COLOR_MODEL, COLOR_ZERO, apply_design3_style, save_figure
from .verification import group14_comparison_config


ATM_PER_BAR = 1.0 / 1.01325
MOL_G_H_TO_MOL_KG_S = 1000.0 / 3600.0

MODEL_COLORS = {
    "full_m4": COLOR_MODEL,
    "kopyscinski_1_2_bar": "#0096C7",
    "quindimil_2_6_bar": "#7B2CBF",
}


@dataclass(frozen=True)
class LiteratureProfile:
    model_key: str
    model_label: str
    validity_note: str
    catalyst_mass_kg: np.ndarray
    molar_flows_mol_s: np.ndarray
    success: bool
    message: str

    @property
    def co_conversion(self) -> np.ndarray:
        inlet_co = self.molar_flows_mol_s[0, INDEX["CO"]]
        return (inlet_co - self.molar_flows_mol_s[:, INDEX["CO"]]) / inlet_co

    def elemental_residuals(self) -> dict[str, float]:
        elemental = self.molar_flows_mol_s @ ELEMENT_MATRIX.T
        scale = np.maximum(np.abs(elemental[0]), 1.0e-30)
        names = ("C", "H", "O", "N")
        return {
            name: float(np.max(np.abs(elemental[:, i] - elemental[0, i])) / scale[i])
            for i, name in enumerate(names)
        }


def kopyscinski_parameters(temperature_k: float) -> dict[str, float]:
    """Corrected Kopyscinski model-12b correlations in bar and kg_cat/s."""
    if temperature_k <= 0.0:
        raise ValueError("Temperature must be positive.")
    return {
        "k1": 3.34e6 * np.exp(-74_000.0 / (R_J_MOL_K * temperature_k)),
        "k2": 9.62e14 * np.exp(-161_740.0 / (R_J_MOL_K * temperature_k)),
        "k_c": 8.10e-6 * np.exp(61_200.0 / (R_J_MOL_K * temperature_k)),
        "k_oh": 3.97e-7 * np.exp(72_650.0 / (R_J_MOL_K * temperature_k)),
        "k_alpha": 9.30e-2 * np.exp(6_500.0 / (R_J_MOL_K * temperature_k)),
        "k_eq_wgs": np.exp(4_400.0 / temperature_k - 4.063),
    }


def kopyscinski_rates(
    partial_pressure_bar: np.ndarray, temperature_k: float
) -> tuple[float, float]:
    """Return positive-forward (CO methanation, WGS) rates in mol/(kg_cat s).

    The adsorption denominator uses sqrt(p_CO), as corrected in the published
    corrigendum to Eqs. 25-26.  The algebra is finite for a dry CO/H2 inlet.
    """
    p_co, p_h2, _, p_h2o, p_co2, _ = np.maximum(partial_pressure_bar, 0.0)
    if p_h2 <= 0.0:
        raise ValueError("Kopyscinski kinetics require positive hydrogen pressure.")
    values = kopyscinski_parameters(temperature_k)
    denominator = (
        1.0
        + values["k_c"] * np.sqrt(p_co)
        + values["k_oh"] * p_h2o / np.sqrt(p_h2)
    ) ** 2
    r_co_methanation = (
        values["k1"]
        * values["k_c"]
        * np.sqrt(p_co)
        * np.sqrt(p_h2)
        / denominator
    )
    r_wgs = values["k2"] * (
        values["k_alpha"] * p_co * p_h2o
        - p_co2 * p_h2 / values["k_eq_wgs"]
    ) / (np.sqrt(p_h2) * denominator)
    return float(r_co_methanation), float(r_wgs)


QUINDIMIL_REFERENCE_TEMPERATURE_K = 350.15 + 273.15


def _reference_shift(
    reference_value: float, energy_j_mol: float, temperature_k: float
) -> float:
    return float(
        reference_value
        * np.exp(
            -energy_j_mol
            / R_J_MOL_K
            * (1.0 / temperature_k - 1.0 / QUINDIMIL_REFERENCE_TEMPERATURE_K)
        )
    )


def quindimil_parameters(temperature_k: float) -> dict[str, float]:
    """Quindimil Table-4 values shifted from the 350.15 C reference row.

    Native pressure is atm and native rate is mol/(g_cat h).  Hydrogen
    adsorption is omitted because its regressed value was not significantly
    different from zero.  The combined formate term is
    K_HCOO = K_CO2*sqrt(K_H2), as reported by the authors.
    """
    if temperature_k <= 0.0:
        raise ValueError("Temperature must be positive.")
    return {
        "k4": _reference_shift(0.299, 91_600.0, temperature_k),
        "k6": _reference_shift(9.01, 26_300.0, temperature_k),
        "k_hcoo": _reference_shift(0.392, -7_860.0, temperature_k),
        "k_oh": _reference_shift(3.86, -26_000.0, temperature_k),
        "k_co": _reference_shift(101.1, -43_200.0, temperature_k),
    }


def quindimil_equilibrium_constants(temperature_k: float) -> tuple[float, float]:
    """Return (K_RWGS, K_CO-methanation) on the paper's atm pressure basis."""
    k_co2_methanation = (
        137.0
        * temperature_k ** -3.998
        * np.exp(158_700.0 / (R_J_MOL_K * temperature_k))
    )
    ln_k_wgs = -3.732 + 3_850.0 / temperature_k + (470.0 / temperature_k) ** 2
    k_rwgs = 1.0 / np.exp(ln_k_wgs)
    k_co_methanation = k_co2_methanation / k_rwgs
    return float(k_rwgs), float(k_co_methanation)


def quindimil_rates(
    partial_pressure_bar: np.ndarray, temperature_k: float
) -> tuple[float, float]:
    """Return positive-forward (CO methanation, RWGS) rates in mol/(kg_cat s)."""
    p_co, p_h2, p_ch4, p_h2o, p_co2, _ = (
        np.maximum(partial_pressure_bar, 0.0) * ATM_PER_BAR
    )
    if p_h2 <= 0.0:
        raise ValueError("Quindimil kinetics require positive hydrogen pressure.")
    values = quindimil_parameters(temperature_k)
    k_eq_rwgs, k_eq_co_methanation = quindimil_equilibrium_constants(temperature_k)
    denominator = (
        1.0
        + values["k_hcoo"] * p_co2 * np.sqrt(p_h2)
        + values["k_oh"] * p_h2o / np.sqrt(p_h2)
        + values["k_co"] * p_co
    ) ** 2
    # Expanded forms avoid 0/0 at dry inlets or when p_CO2 is initially zero.
    r_rwgs_native = values["k4"] * (
        p_co2 * np.sqrt(p_h2)
        - p_co * p_h2o / (np.sqrt(p_h2) * k_eq_rwgs)
    ) / denominator
    r_co_methanation_native = values["k6"] * (
        p_co * np.sqrt(p_h2)
        - p_ch4 * p_h2o / (p_h2**2.5 * k_eq_co_methanation)
    ) / denominator
    return (
        float(r_co_methanation_native * MOL_G_H_TO_MOL_KG_S),
        float(r_rwgs_native * MOL_G_H_TO_MOL_KG_S),
    )


def _simulate_literature_model(
    *,
    model_key: str,
    model_label: str,
    validity_note: str,
    inlet_flows_mol_s: np.ndarray,
    temperature_k: float,
    pressure_bar: float,
    catalyst_mass_kg: float,
    rate_function: Callable[[np.ndarray, float], tuple[float, float]],
    second_reaction_is_rwgs: bool,
    output_points: int = 101,
) -> LiteratureProfile:
    """Integrate one literature rate pair on the shared Experiment 1 basis."""
    y0 = np.asarray(inlet_flows_mol_s, dtype=float)
    atol = np.full(len(SPECIES), 1.0e-14)

    def rhs(_: float, flows: np.ndarray) -> np.ndarray:
        if np.min(flows) < -1.0e-12:
            raise ValueError(f"{model_label} produced a materially negative flow.")
        safe_flows = np.maximum(flows, 0.0)
        total_flow = float(safe_flows.sum())
        if total_flow <= 0.0:
            raise ValueError(f"{model_label} produced non-positive total flow.")
        partial_pressure_bar = safe_flows / total_flow * pressure_bar
        r_co_methanation, r_second = rate_function(
            partial_pressure_bar, temperature_k
        )
        if second_reaction_is_rwgs:
            paper_direction_rates = np.array([0.0, r_co_methanation, r_second])
        else:
            # STOICH_FULL's third column is RWGS, so forward WGS is negative.
            paper_direction_rates = np.array([0.0, r_co_methanation, -r_second])
        return STOICH_FULL @ paper_direction_rates

    grid = np.linspace(0.0, catalyst_mass_kg, output_points)
    solution = solve_ivp(
        rhs,
        (0.0, catalyst_mass_kg),
        y0,
        method="Radau",
        rtol=1.0e-8,
        atol=atol,
        t_eval=grid,
    )
    completed = bool(
        solution.success
        and len(solution.t) == output_points
        and np.isclose(solution.t[-1], catalyst_mass_kg, rtol=0.0, atol=1.0e-12)
        and np.min(solution.y) >= -1.0e-12
    )
    return LiteratureProfile(
        model_key=model_key,
        model_label=model_label,
        validity_note=validity_note,
        catalyst_mass_kg=solution.t,
        molar_flows_mol_s=solution.y.T,
        success=completed,
        message=solution.message,
    )


def run_three_model_verification(data: dict) -> tuple[dict, object, LiteratureProfile, LiteratureProfile]:
    """Run full M4, Kopyscinski, and Quindimil at the same 1 bar conditions."""
    pressure_bar = 1.0
    m4_comparison, m4_result = compare_experiment1(
        data, pressure_bar=pressure_bar, reaction_mode="m4_full"
    )
    model_data = _model_input_data(data, pressure_bar=pressure_bar)
    shared_config = group14_comparison_config(model_data, reaction_mode="m4_full")
    common = {
        "inlet_flows_mol_s": shared_config.inlet_flows_mol_s,
        "temperature_k": shared_config.feed.temperature_k,
        "pressure_bar": pressure_bar,
        "catalyst_mass_kg": shared_config.catalyst_mass_kg,
    }
    kopyscinski = _simulate_literature_model(
        model_key="kopyscinski_1_2_bar",
        model_label="Kopyscinski",
        validity_note="Published 1-2 bar range; evaluated at 1 bar.",
        rate_function=kopyscinski_rates,
        second_reaction_is_rwgs=False,
        **common,
    )
    quindimil = _simulate_literature_model(
        model_key="quindimil_2_6_bar",
        model_label="Quindimil",
        validity_note="Published 2-6 bar range; 1 bar is a pressure extrapolation.",
        rate_function=quindimil_rates,
        second_reaction_is_rwgs=True,
        **common,
    )
    return m4_comparison.to_dict(), m4_result, kopyscinski, quindimil


def _plot_three_models(
    *,
    observed_conversion_fraction: float,
    m4_result,
    kopyscinski: LiteratureProfile,
    quindimil: LiteratureProfile,
    output_path: Path,
) -> None:
    apply_design3_style(font_size=10.0)
    from matplotlib.gridspec import GridSpec

    profiles = (
        (
            f"Full M4: {m4_result.co_conversion[-1] * 100.0:.2f}% "
            "(5-15 bar fit; extrapolated)",
            m4_result.catalyst_mass_kg,
            m4_result.co_conversion,
            MODEL_COLORS["full_m4"],
        ),
        (
            f"Kopyscinski: {kopyscinski.co_conversion[-1] * 100.0:.2f}% "
            "(1-2 bar fit)",
            kopyscinski.catalyst_mass_kg,
            kopyscinski.co_conversion,
            MODEL_COLORS["kopyscinski_1_2_bar"],
        ),
        (
            f"Quindimil: {quindimil.co_conversion[-1] * 100.0:.2f}% "
            "(2-6 bar fit; extrapolated)",
            quindimil.catalyst_mass_kg,
            quindimil.co_conversion,
            MODEL_COLORS["quindimil_2_6_bar"],
        ),
    )
    catalyst_mass_g = float(m4_result.catalyst_mass_kg[-1] * 1000.0)
    observed_pct = observed_conversion_fraction * 100.0

    fig = plt.figure(figsize=(6.2, 5.2))
    gs = GridSpec(2, 1, height_ratios=[3.2, 1.0], hspace=0.10)
    ax_main = fig.add_subplot(gs[0])
    ax_res = fig.add_subplot(gs[1], sharex=ax_main)

    endpoint_residuals: list[tuple[str, float, str]] = []
    for label, mass_kg, conversion, color in profiles:
        ax_main.plot(
            mass_kg * 1000.0,
            conversion * 100.0,
            color=color,
            linewidth=1.8,
            label=label,
            zorder=3,
        )
        endpoint_residuals.append((label, float(conversion[-1] * 100.0 - observed_pct), color))

    ax_main.plot(
        [catalyst_mass_g],
        [observed_pct],
        marker="o",
        linestyle="none",
        color=COLOR_EXP,
        markerfacecolor="#FFFFFF",
        markeredgewidth=1.8,
        markersize=6.8,
        label="Experiment 1 observed",
        zorder=5,
    )
    ax_main.annotate(
        rf"Exp 1: {observed_pct:.3f}$\%$",
        xy=(catalyst_mass_g, observed_pct),
        xytext=(catalyst_mass_g - 1.25, observed_pct + 12.0),
        arrowprops=dict(
            arrowstyle="->",
            connectionstyle="arc3,rad=-0.15",
            color=COLOR_EXP,
            lw=1.1,
        ),
        fontsize=8.8,
        fontweight="bold",
        color=COLOR_EXP,
        zorder=6,
    )
    ax_main.text(
        0.03,
        0.94,
        "a",
        transform=ax_main.transAxes,
        fontsize=13,
        fontweight="bold",
        va="top",
    )
    ax_main.text(
        0.97,
        0.96,
        r"$T=350\,^\circ\mathrm{C},\ P=1.00\,\mathrm{bar}$",
        transform=ax_main.transAxes,
        fontsize=8.5,
        ha="right",
        va="top",
    )
    ax_main.set_ylabel(r"$\mathrm{CO}$ Conversion, $X_{\mathrm{CO}}$ [$\%$]", labelpad=6)
    ax_main.set_xlim(0.0, max(catalyst_mass_g * 1.05, 3.2))
    ax_main.set_ylim(0.0, 105.0)
    ax_main.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax_main.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax_main.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    plt.setp(ax_main.get_xticklabels(), visible=False)
    ax_main.legend(
        loc="lower right",
        bbox_to_anchor=(0.97, 0.05),
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#D0D0D0",
        framealpha=0.94,
        handlelength=2.0,
        handletextpad=0.6,
        labelspacing=0.4,
    )

    ax_res.axhline(0.0, color=COLOR_ZERO, linestyle="--", linewidth=0.85, zorder=2)
    for _, residual, color in endpoint_residuals:
        ax_res.plot(
            [catalyst_mass_g],
            [residual],
            marker="s",
            linestyle="none",
            color=color,
            markersize=5.2,
            zorder=4,
        )
    max_abs = max(abs(item[1]) for item in endpoint_residuals)
    ax_res.set_ylim(-max(max_abs * 1.25, 5.0), max(max_abs * 1.25, 5.0))
    ax_res.set_xlabel(r"Catalyst Mass, $W$ [$\mathrm{g}$]", labelpad=6)
    ax_res.set_ylabel(r"$\Delta X_{\mathrm{CO}}$ [pp]", labelpad=6)
    ax_res.tick_params(top=False)
    ax_res.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    save_figure(fig, output_path, dpi=300, tight=False)


def write_outputs(data: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    m4_comparison, m4_result, kopyscinski, quindimil = run_three_model_verification(data)
    if not m4_result.success or m4_result.terminal_event is not None:
        raise RuntimeError(f"Full M4 failed: {m4_result.message}")
    for profile in (kopyscinski, quindimil):
        if not profile.success:
            raise RuntimeError(f"{profile.model_label} failed: {profile.message}")

    observed = float(data["reported_metrics"]["co_conversion_fraction"])
    model_records = {
        "full_m4": {
            **m4_comparison,
            "model_label": "Full M4",
            "published_pressure_range_bar": [5.0, 15.0],
            "pressure_status": "extrapolated below fitted range",
            "feed_scope_status": "CO/H2 feed is within the model's studied reaction families",
            "elemental_residuals": m4_result.elemental_residuals(),
        },
        kopyscinski.model_key: {
            "model_label": kopyscinski.model_label,
            "published_pressure_range_bar": [1.0, 2.0],
            "pressure_status": "within published range",
            "feed_scope_status": "CO/H2 feed matches the model's primary CO-methanation scope",
            "predicted_co_conversion_fraction": float(kopyscinski.co_conversion[-1]),
            "experimental_co_conversion_fraction": observed,
            "signed_error_percentage_points": float(
                100.0 * (kopyscinski.co_conversion[-1] - observed)
            ),
            "solver_success": kopyscinski.success,
            "solver_message": kopyscinski.message,
            "elemental_residuals": kopyscinski.elemental_residuals(),
        },
        quindimil.model_key: {
            "model_label": quindimil.model_label,
            "published_pressure_range_bar": [2.0, 6.0],
            "pressure_status": "extrapolated below fitted range",
            "feed_scope_status": "CO/H2 feed extrapolates beyond the model's CO2/H2 fitting scope",
            "predicted_co_conversion_fraction": float(quindimil.co_conversion[-1]),
            "experimental_co_conversion_fraction": observed,
            "signed_error_percentage_points": float(
                100.0 * (quindimil.co_conversion[-1] - observed)
            ),
            "solver_success": quindimil.success,
            "solver_message": quindimil.message,
            "elemental_residuals": quindimil.elemental_residuals(),
        },
    }
    payload = {
        "comparison_type": "three independent no-fit models versus Experiment 1",
        "shared_conditions": {
            "pressure_bar_absolute": 1.0,
            "temperature_c": float(data["basis"]["reaction_temperature_c"]),
            "catalyst_mass_g": float(data["basis"]["catalyst_mass_g"]),
            "inlet_molar_flow_mol_h": data["inlet_molar_flow_mol_h"],
            "thermal_mode": "isothermal",
            "transport_mode": "constant_pressure",
        },
        "reported_co_conversion_fraction": observed,
        "models": model_records,
        "interpretation": (
            "The curves are independent literature-model predictions at identical conditions. "
            "They are not pressure-spliced and no kinetic parameter was fitted to Experiment 1."
        ),
    }
    (output_dir / "experiment1_model_comparison.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    (output_dir / "experiment1_data_audit.json").write_text(
        json.dumps(audit_experiment1_data(data), indent=2), encoding="utf-8"
    )
    _plot_three_models(
        observed_conversion_fraction=observed,
        m4_result=m4_result,
        kopyscinski=kopyscinski,
        quindimil=quindimil,
        output_path=output_dir / "experiment1_co_conversion_comparison.png",
    )

    rows = []
    for key in ("full_m4", "kopyscinski_1_2_bar", "quindimil_2_6_bar"):
        record = model_records[key]
        rows.append(
            f"| {record['model_label']} | {record['predicted_co_conversion_fraction']:.3%} "
            f"| {record['signed_error_percentage_points']:+.2f} pp | "
            f"{record['pressure_status']} |"
        )
    report = f"""# Experiment 1 three-model CO-conversion verification

All three models were evaluated independently at **1.00 bar absolute**, 350 °C,
3.12 g catalyst, and the unchanged Experiment 1 inlet flows: N2 0.799 mol/h,
H2 0.959 mol/h, and CO 0.320 mol/h. Operation is isothermal and at constant
pressure. No kinetic or activity parameter was fitted to the reported 40.630%
CO conversion.

| Model | Predicted CO conversion | Prediction - experiment | Pressure-domain status |
|---|---:|---:|---|
{chr(10).join(rows)}

The curves are not stitched together. Kopyscinski is evaluated inside its
published 1-2 bar range. Quindimil is shown at the user-requested 1 bar even
though its published kinetic range begins at 2 bar, and full M4 is likewise a
pressure extrapolation below its 5-15 bar fit range. Catalyst formulations also
differ among the literature models, so agreement or disagreement is a no-fit
transferability comparison rather than parameter validation.

The Quindimil curve is additionally a feed-composition extrapolation because
its parameters were fitted to CO2/H2 experiments, whereas Experiment 1 starts
with CO/H2/N2. It is included because the user requested all three models at the
same one-bar condition, not because it is claimed as an in-domain validation.

The Kopyscinski implementation uses the published corrigendum's
sqrt(p_CO) adsorption term. The Quindimil implementation retains its native atm
and mol/(g_cat h) parameter basis internally, then converts rates to mol/(kg_cat s)
for integration on the common catalyst-mass coordinate.
"""
    (output_dir / "EXPERIMENT1_VERIFICATION_AUDIT.md").write_text(
        report, encoding="utf-8"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare full M4 and two low-pressure literature models at 1 bar."
    )
    parser.add_argument("--data", required=True, help="Experiment 1 JSON transcription")
    parser.add_argument("--output", required=True, help="Verification output directory")
    args = parser.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    payload = write_outputs(data, Path(args.output))
    for key, record in payload["models"].items():
        print(f"{key}_co_conversion={record['predicted_co_conversion_fraction']:.6f}")
    print(f"reported_co_conversion={payload['reported_co_conversion_fraction']:.6f}")
    print(f"outputs={Path(args.output).resolve()}")


if __name__ == "__main__":
    main()

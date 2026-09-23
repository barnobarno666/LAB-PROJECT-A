"""Coupled mass, energy, and pressure balances for reduced M4 operation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .config import ReactorConfig
from .constants import ELEMENT_MATRIX, ELEMENTS, INDEX, MOLECULAR_WEIGHT_KG_MOL, PA_PER_BAR, R_J_MOL_K, SPECIES
from .kinetics import rates_reduced_m4
from .thermo import cp_species_j_mol_k, reaction_enthalpies_j_mol


@dataclass(frozen=True)
class SimulationResult:
    config: ReactorConfig
    catalyst_mass_kg: np.ndarray
    molar_flows_mol_s: np.ndarray
    temperature_k: np.ndarray
    pressure_pa: np.ndarray
    success: bool
    message: str
    nfev: int
    terminal_event: str | None

    @property
    def bed_length_m(self) -> np.ndarray:
        return self.catalyst_mass_kg / (
            self.config.bed.catalyst_loading_kg_m3_bed * self.config.cross_section_m2
        )

    @property
    def total_flow_mol_s(self) -> np.ndarray:
        return self.molar_flows_mol_s.sum(axis=1)

    @property
    def mole_fractions(self) -> np.ndarray:
        return self.molar_flows_mol_s / self.total_flow_mol_s[:, None]

    @property
    def partial_pressures_bar(self) -> np.ndarray:
        return self.mole_fractions * self.pressure_pa[:, None] / PA_PER_BAR

    @property
    def concentrations_mol_m3(self) -> np.ndarray:
        return self.mole_fractions * self.pressure_pa[:, None] / (R_J_MOL_K * self.temperature_k[:, None])

    @property
    def co_conversion(self) -> np.ndarray:
        inlet = self.molar_flows_mol_s[0, INDEX["CO"]]
        return (inlet - self.molar_flows_mol_s[:, INDEX["CO"]]) / inlet

    @property
    def methane_yield(self) -> np.ndarray:
        inlet_co = self.molar_flows_mol_s[0, INDEX["CO"]]
        return (self.molar_flows_mol_s[:, INDEX["CH4"]] - self.molar_flows_mol_s[0, INDEX["CH4"]]) / inlet_co

    def elemental_residuals(self) -> dict[str, float]:
        elemental_flows = self.molar_flows_mol_s @ ELEMENT_MATRIX.T
        inlet = elemental_flows[0]
        scales = np.maximum(np.abs(inlet), 1.0e-30)
        return {
            element: float(np.max(np.abs(elemental_flows[:, i] - inlet[i])) / scales[i])
            for i, element in enumerate(ELEMENTS)
        }


def _local_properties(config: ReactorConfig, y: np.ndarray) -> tuple[np.ndarray, float, float, float, float]:
    flows = y[: len(SPECIES)]
    temperature_k = y[-2]
    pressure_pa = y[-1]
    if np.any(flows < -10.0 * config.solver.atol_flow_mol_s):
        raise ValueError("Accepted integration state has materially negative molar flow.")
    safe_flows = np.maximum(flows, 0.0)
    total_flow = safe_flows.sum()
    if total_flow <= 0.0:
        raise ValueError("Total molar flow is non-positive.")
    mole_fraction = safe_flows / total_flow
    partial_pressure_bar = mole_fraction * pressure_pa / PA_PER_BAR
    average_mw = float(mole_fraction @ MOLECULAR_WEIGHT_KG_MOL)
    superficial_velocity = total_flow * R_J_MOL_K * temperature_k / (pressure_pa * config.cross_section_m2)
    gas_density = pressure_pa * average_mw / (R_J_MOL_K * temperature_k)
    return partial_pressure_bar, total_flow, superficial_velocity, gas_density, average_mw


def reactor_rhs(catalyst_mass_kg: float, y: np.ndarray, config: ReactorConfig) -> np.ndarray:
    """Return dY/dW using W = kg catalyst as the independent coordinate."""
    partial_pressure_bar, _, superficial_velocity, gas_density, _ = _local_properties(config, y)
    flows = y[: len(SPECIES)]
    temperature_k = y[-2]
    pressure_pa = y[-1]
    r_co_methanation, r_wgs = rates_reduced_m4(partial_pressure_bar, temperature_k)
    a = config.activity

    derivatives = np.zeros_like(y)
    derivatives[INDEX["CO"]] = -a * (r_co_methanation + r_wgs)
    derivatives[INDEX["H2"]] = a * (-3.0 * r_co_methanation + r_wgs)
    derivatives[INDEX["CH4"]] = a * r_co_methanation
    derivatives[INDEX["H2O"]] = a * (r_co_methanation - r_wgs)
    derivatives[INDEX["CO2"]] = a * r_wgs

    if config.thermal.mode == "isothermal":
        derivatives[-2] = 0.0
    else:
        heat_capacity_flow = float(flows @ cp_species_j_mol_k(temperature_k))
        dh_co_methanation = reaction_enthalpies_j_mol(temperature_k)[1]
        dh_wgs = -reaction_enthalpies_j_mol(temperature_k)[2]
        reaction_heat_w_kg = a * (-dh_co_methanation * r_co_methanation - dh_wgs * r_wgs)
        wall_heat_w_kg = 0.0
        if config.thermal.mode == "heat_exchange":
            area_per_bed_volume = 4.0 / config.bed.tube_diameter_m
            wall_heat_w_kg = (
                config.thermal.overall_heat_transfer_w_m2_k
                * area_per_bed_volume
                / config.bed.catalyst_loading_kg_m3_bed
                * (temperature_k - config.thermal.wall_temperature_k)
            )
        derivatives[-2] = (reaction_heat_w_kg - wall_heat_w_kg) / heat_capacity_flow

    if config.transport.mode == "constant_pressure":
        derivatives[-1] = 0.0
    else:
        eps = config.bed.void_fraction
        dp = config.bed.particle_diameter_m
        ergun_pa_m = (
            150.0 * config.transport.gas_viscosity_pa_s * (1.0 - eps) ** 2 * superficial_velocity / (dp**2 * eps**3)
            + 1.75 * gas_density * (1.0 - eps) * superficial_velocity**2 / (dp * eps**3)
        )
        derivatives[-1] = -ergun_pa_m / (config.bed.catalyst_loading_kg_m3_bed * config.cross_section_m2)
    return derivatives


def _initial_state(config: ReactorConfig) -> np.ndarray:
    return np.concatenate(
        [config.inlet_flows_mol_s, [config.feed.temperature_k, config.inlet_pressure_pa]]
    )


def simulate(config: ReactorConfig) -> SimulationResult:
    """Integrate the configured bed and return profiles in the configured coordinate."""
    y0 = _initial_state(config)
    atol = np.array(
        [config.solver.atol_flow_mol_s] * len(SPECIES)
        + [config.solver.atol_temperature_k, config.solver.atol_pressure_pa]
    )

    def pressure_event(_: float, y: np.ndarray) -> float:
        return y[-1] - config.solver.min_pressure_pa

    def temperature_event(_: float, y: np.ndarray) -> float:
        return config.solver.max_temperature_k - y[-2]

    def hydrogen_event(_: float, y: np.ndarray) -> float:
        flows = np.maximum(y[: len(SPECIES)], 0.0)
        total = flows.sum()
        if total <= 0.0:
            return -1.0
        p_h2_bar = flows[INDEX["H2"]] / total * y[-1] / PA_PER_BAR
        return p_h2_bar - config.solver.min_hydrogen_partial_pressure_bar

    for event in (pressure_event, temperature_event, hydrogen_event):
        event.terminal = True
        event.direction = -1.0

    solution = solve_ivp(
        fun=lambda w, state: reactor_rhs(w, state, config),
        t_span=(0.0, config.catalyst_mass_kg),
        y0=y0,
        method=config.solver.method,
        rtol=config.solver.rtol,
        atol=atol,
        dense_output=True,
        events=(pressure_event, temperature_event, hydrogen_event),
    )
    endpoint = float(solution.t[-1])
    points = np.linspace(0.0, endpoint, config.solver.output_points)
    states = solution.sol(points).T if solution.sol is not None else solution.y.T
    terminal_event = None
    labels = ("minimum_pressure", "maximum_temperature", "minimum_hydrogen")
    for label, times in zip(labels, solution.t_events):
        if len(times):
            terminal_event = label
            break
    completed_bed = np.isclose(endpoint, config.catalyst_mass_kg, rtol=0.0, atol=1e-12)
    accepted_flows = states[:, : len(SPECIES)]
    materially_negative = np.min(accepted_flows) < -10.0 * config.solver.atol_flow_mol_s
    success = bool(solution.success and completed_bed and terminal_event is None and not materially_negative)
    message = solution.message
    if terminal_event:
        message = f"{message} Terminal event: {terminal_event}."
    if materially_negative:
        message = f"{message} Accepted profile contains materially negative molar flow."
    return SimulationResult(
        config=config,
        catalyst_mass_kg=points,
        molar_flows_mol_s=states[:, : len(SPECIES)],
        temperature_k=states[:, -2],
        pressure_pa=states[:, -1],
        success=success,
        message=message,
        nfev=solution.nfev,
        terminal_event=terminal_event,
    )

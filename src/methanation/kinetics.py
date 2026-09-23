"""Published M4 constants and signed full or reduced reaction rates."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .constants import R_J_MOL_K
from .thermo import equilibrium_constants

KINETIC_REFERENCE_TEMPERATURE_K = 598.0


@dataclass(frozen=True)
class M4Parameters:
    """Celoria et al. (2025), Table 5, M4 central estimates."""

    k_ref_mol_kg_s_bar_15: np.ndarray = field(
        default_factory=lambda: np.array([0.0168, 1.50, 0.119])
    )
    activation_energy_j_mol: np.ndarray = field(
        default_factory=lambda: np.array([118_000.0, 54_900.0, 110_000.0])
    )
    kh2_ref_bar_inverse: float = 0.500
    dh_ads_h2_j_mol: float = -8_760.0
    kco_ref_bar_inverse: float = 1.41
    dh_ads_co_j_mol: float = -38_500.0
    kc_ref_bar: float = 1.78
    dh_ads_c_j_mol: float = -20_000.0
    kch4_ref_bar_inverse: float = 0.500
    dh_ads_ch4_j_mol: float = 18_800.0


DEFAULT_PARAMETERS = M4Parameters()


def _shift_reference(value_ref: np.ndarray | float, enthalpy_j_mol: np.ndarray | float, temperature_k: float):
    return value_ref * np.exp(
        -np.asarray(enthalpy_j_mol) / R_J_MOL_K
        * (1.0 / temperature_k - 1.0 / KINETIC_REFERENCE_TEMPERATURE_K)
    )


def kinetic_constants(temperature_k: float, parameters: M4Parameters = DEFAULT_PARAMETERS) -> np.ndarray:
    if temperature_k <= 0.0:
        raise ValueError("Temperature must be positive.")
    return _shift_reference(
        parameters.k_ref_mol_kg_s_bar_15,
        parameters.activation_energy_j_mol,
        temperature_k,
    )


def adsorption_constants(temperature_k: float, parameters: M4Parameters = DEFAULT_PARAMETERS) -> dict[str, float]:
    if temperature_k <= 0.0:
        raise ValueError("Temperature must be positive.")
    return {
        "H2": float(_shift_reference(parameters.kh2_ref_bar_inverse, parameters.dh_ads_h2_j_mol, temperature_k)),
        "CO": float(_shift_reference(parameters.kco_ref_bar_inverse, parameters.dh_ads_co_j_mol, temperature_k)),
        "C": float(_shift_reference(parameters.kc_ref_bar, parameters.dh_ads_c_j_mol, temperature_k)),
        "CH4": float(_shift_reference(parameters.kch4_ref_bar_inverse, parameters.dh_ads_ch4_j_mol, temperature_k)),
    }


def adsorption_denominator(partial_pressure_bar: np.ndarray, temperature_k: float, parameters: M4Parameters = DEFAULT_PARAMETERS) -> float:
    """M4 shared adsorption denominator, using [CO, H2, CH4, H2O, CO2, N2]."""
    p_co, p_h2, p_ch4, _, _, _ = partial_pressure_bar
    if p_h2 <= 0.0:
        raise ValueError("M4 denominator requires positive hydrogen partial pressure.")
    ads = adsorption_constants(temperature_k, parameters)
    return float(
        1.0
        + np.sqrt(ads["H2"] * p_h2)
        + ads["CO"] * p_co
        + ads["C"] * p_ch4 / p_h2**2
        + ads["CH4"] * p_ch4
    )


def rates_reduced_m4(
    partial_pressure_bar: np.ndarray,
    temperature_k: float,
    parameters: M4Parameters = DEFAULT_PARAMETERS,
) -> tuple[float, float]:
    """Return signed (CO methanation, WGS) net rates in mol/(kg catalyst s).

    WGS is the negative of Celoria's published RWGS rate. The expressions are
    algebraically expanded so a dry CO/H2/N2 inlet is finite in reduced mode.
    """
    p_co, p_h2, p_ch4, p_h2o, p_co2, _ = partial_pressure_bar
    if np.any(partial_pressure_bar < 0.0):
        raise ValueError("Partial pressures cannot be negative.")
    if p_h2 <= 0.0:
        raise ValueError("Reduced M4 rates require positive hydrogen partial pressure.")
    denominator = adsorption_denominator(partial_pressure_bar, temperature_k, parameters)
    _, k2, k3 = kinetic_constants(temperature_k, parameters)
    _, keq_co, keq_rwgs = equilibrium_constants(temperature_k)

    r_co_methanation = k2 / denominator**2 * (
        p_co * np.sqrt(p_h2) - p_ch4 * p_h2o / (keq_co * p_h2**2.5)
    )
    r_rwgs = k3 / denominator**2 * (
        p_co2 * np.sqrt(p_h2) - p_co * p_h2o / (keq_rwgs * np.sqrt(p_h2))
    )
    return float(r_co_methanation), float(-r_rwgs)


def rates_full_m4(
    partial_pressure_bar: np.ndarray,
    temperature_k: float,
    parameters: M4Parameters = DEFAULT_PARAMETERS,
) -> tuple[float, float, float]:
    """Return signed (CO2 methanation, CO methanation, WGS) rates.

    The published M4 reaction 1 divides by water pressure. At a dry
    CO/H2 inlet with no CO2 its rate has a zero limit along the physical
    solution; the reactor uses a derived near-inlet start for integration.
    A dry inlet already containing CO2 has no finite M4 reaction-1 rate.
    """
    _, p_h2, p_ch4, p_h2o, p_co2, _ = partial_pressure_bar
    r_co, r_wgs = rates_reduced_m4(partial_pressure_bar, temperature_k, parameters)
    if p_h2o == 0.0:
        if p_co2 > 0.0:
            raise ValueError("Full M4 CO2 methanation requires water when CO2 is present.")
        return 0.0, r_co, r_wgs

    denominator = adsorption_denominator(partial_pressure_bar, temperature_k, parameters)
    k1 = kinetic_constants(temperature_k, parameters)[0]
    keq_co2 = equilibrium_constants(temperature_k)[0]
    r_co2 = k1 / denominator**2 * (
        p_co2 * p_h2**1.5 / p_h2o
        - p_ch4 * p_h2o / (keq_co2 * p_h2**2.5)
    )
    return float(r_co2), r_co, r_wgs

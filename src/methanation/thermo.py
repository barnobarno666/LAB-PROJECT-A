"""Thermochemical closure for the initial reduced-M4 implementation."""

from __future__ import annotations

import numpy as np

from .constants import CP_J_MOL_K, R_J_MOL_K

T_REF_K = 298.15

# Reaction order: CO2 methanation, CO methanation, RWGS.
# Values derive from the reaction values reported on paper page 3, with reaction 1
# adjusted to reaction 2 + reaction 3 so the three-reaction cycle closes exactly.
REACTION_DH_J_MOL = np.array([-165_000.0, -206_000.0, 41_000.0])
REACTION_DG_REF_J_MOL = np.array([-113_000.0, -142_000.0, 29_000.0])


def cp_species_j_mol_k(temperature_k: float) -> np.ndarray:
    """Return species heat capacities.

    This initial implementation uses a constant-Cp approximation. The argument is
    retained so a temperature-dependent, cited correlation is a drop-in upgrade.
    """
    if temperature_k <= 0.0:
        raise ValueError("Temperature must be positive.")
    return CP_J_MOL_K.copy()


def reaction_enthalpies_j_mol(temperature_k: float) -> np.ndarray:
    """Return reaction enthalpies in the paper's forward reaction directions."""
    if temperature_k <= 0.0:
        raise ValueError("Temperature must be positive.")
    return REACTION_DH_J_MOL.copy()


def equilibrium_constants(temperature_k: float) -> np.ndarray:
    """Return dimensionless K_eq values in the paper's forward directions.

    A constant reaction-enthalpy van't Hoff approximation is used. The same
    reference Gibbs energies and enthalpies are used for all reactions, preserving
    K1 = K2 * K3 exactly.
    """
    if temperature_k <= 0.0:
        raise ValueError("Temperature must be positive.")
    k_ref = np.exp(-REACTION_DG_REF_J_MOL / (R_J_MOL_K * T_REF_K))
    return k_ref * np.exp(
        -REACTION_DH_J_MOL / R_J_MOL_K * (1.0 / temperature_k - 1.0 / T_REF_K)
    )

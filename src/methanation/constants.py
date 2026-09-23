"""Species and reaction constants with one explicit internal unit contract."""

from __future__ import annotations

import numpy as np

R_J_MOL_K = 8.31446261815324
PA_PER_BAR = 100_000.0

SPECIES = ("CO", "H2", "CH4", "H2O", "CO2", "N2")
INDEX = {name: i for i, name in enumerate(SPECIES)}

# kg/mol, ordered as SPECIES.
MOLECULAR_WEIGHT_KG_MOL = np.array(
    [28.0101e-3, 2.01588e-3, 16.04246e-3, 18.01528e-3, 44.0095e-3, 28.0134e-3]
)

# C, H, O, N elemental atom counts by species. Used for conservation checks.
ELEMENT_MATRIX = np.array(
    [
        [1.0, 0.0, 1.0, 0.0, 1.0, 0.0],
        [0.0, 2.0, 4.0, 2.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 1.0, 2.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 2.0],
    ]
)
ELEMENTS = ("C", "H", "O", "N")

# Rows = SPECIES, columns = [CO2 methanation, CO methanation, RWGS].
STOICH_FULL = np.array(
    [
        [0.0, -1.0, 1.0],
        [-4.0, -3.0, -1.0],
        [1.0, 1.0, 0.0],
        [2.0, 1.0, 1.0],
        [-1.0, 0.0, -1.0],
        [0.0, 0.0, 0.0],
    ]
)

# Constant-Cp approximation near the project temperature range. Values are J/(mol K).
# They are deliberately centralized so a cited Shomate/NASA model can replace this module.
CP_J_MOL_K = np.array([30.3, 29.3, 52.0, 36.5, 46.5, 30.1])

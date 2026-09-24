import json
from pathlib import Path

import numpy as np

from methanation.experiment1_three_model_verification import (
    QUINDIMIL_REFERENCE_TEMPERATURE_K,
    kopyscinski_rates,
    quindimil_parameters,
    run_three_model_verification,
)


DATA_PATH = Path(__file__).parents[1] / "data" / "experiment1_observed_data.json"


def test_quindimil_reference_parameters_match_table_4():
    values = quindimil_parameters(QUINDIMIL_REFERENCE_TEMPERATURE_K)
    assert values == {
        "k4": 0.299,
        "k6": 9.01,
        "k_hcoo": 0.392,
        "k_oh": 3.86,
        "k_co": 101.1,
    }


def test_corrected_kopyscinski_rates_are_finite_at_dry_co_feed():
    rates = kopyscinski_rates(
        np.array([0.15, 0.45, 0.0, 0.0, 0.0, 0.40]), 623.15
    )
    assert np.all(np.isfinite(rates))
    assert rates[0] > 0.0
    assert rates[1] == 0.0


def test_three_models_use_same_one_bar_experiment_basis_and_complete():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    m4, m4_result, kopyscinski, quindimil = run_three_model_verification(data)
    assert m4["inlet_pressure_bar"] == 1.0
    assert m4_result.success and m4_result.terminal_event is None
    assert kopyscinski.success
    assert quindimil.success
    for profile in (kopyscinski, quindimil):
        assert np.isclose(profile.catalyst_mass_kg[-1], 0.00312)
        assert 0.0 <= profile.co_conversion[-1] <= 1.0
        assert max(profile.elemental_residuals().values()) < 1.0e-8

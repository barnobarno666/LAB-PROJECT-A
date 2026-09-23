import json
from pathlib import Path

from methanation.verification import audit_group14_data, compare_group14_experiment


DATA_PATH = Path(__file__).parents[1] / "data" / "group14_observed_data.json"


def test_group14_data_audit_detects_nonphysical_closure():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    audit = audit_group14_data(data)
    assert abs(audit.normalized_fraction_sum - 1.0) < 5e-4
    assert not audit.physically_reconcilable
    assert audit.carbon_relative_residual > 0.3
    assert audit.oxygen_relative_residual > 0.7
    assert audit.water_from_oxygen_balance_mol_h < 0.0
    assert abs(audit.tracer_co_conversion_fraction - audit.reported_co_conversion_fraction) > 0.5


def test_group14_comparison_uses_reported_conversion_as_benchmark():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    comparison, result = compare_group14_experiment(data)
    assert result.success, result.message
    assert comparison.experimental_co_conversion_fraction == data["reported_metrics"]["co_conversion_fraction"]
    assert 0.0 < comparison.predicted_co_conversion_fraction < 1.0
    assert comparison.signed_error_percentage_points < 0.0

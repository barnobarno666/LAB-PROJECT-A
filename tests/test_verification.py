import json
from dataclasses import replace
from pathlib import Path

from methanation.verification import audit_group14_data, compare_group14_experiment
from methanation.experiment_verification import compare_experiment1
from methanation.reactor import simulate


DATA_PATH = Path(__file__).parents[1] / "data" / "group14_observed_data.json"
EXPERIMENT1_DATA_PATH = Path(__file__).parents[1] / "data" / "experiment1_observed_data.json"


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
    assert comparison.reaction_mode == "m4_full"
    assert comparison.experimental_co_conversion_fraction == data["reported_metrics"]["co_conversion_fraction"]
    assert 0.0 < comparison.predicted_co_conversion_fraction < 1.0
    assert comparison.signed_error_percentage_points < 0.0


def test_full_m4_dry_inlet_prediction_is_stable_across_solver_tolerances():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _, reference = compare_group14_experiment(data)
    alternative = simulate(
        replace(
            reference.config,
            solver=replace(
                reference.config.solver,
                rtol=1e-6,
                atol_flow_mol_s=1e-12,
            ),
        )
    )
    assert reference.success and alternative.success
    assert abs(reference.co_conversion[-1] - alternative.co_conversion[-1]) < 1e-5


def test_experiment1_atmospheric_full_m4_reaches_the_bed_endpoint():
    data = json.loads(EXPERIMENT1_DATA_PATH.read_text(encoding="utf-8"))
    comparison, result = compare_experiment1(data, pressure_bar=1.0)
    assert comparison.solver_success
    assert result.terminal_event is None
    assert 0.0 < comparison.predicted_co_conversion_fraction < 1.0

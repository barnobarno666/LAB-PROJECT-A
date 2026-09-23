from dataclasses import replace
from pathlib import Path

import numpy as np

from methanation.config import ReactorConfig
from methanation.constants import INDEX
from methanation.reactor import simulate


CONFIG_PATH = Path(__file__).parents[1] / "configs" / "assumed_base_case.json"


def test_isothermal_constant_pressure_solution_conserves_elements():
    original = ReactorConfig.from_json(CONFIG_PATH)
    config = replace(
        original,
        thermal=replace(original.thermal, mode="isothermal"),
        transport=replace(original.transport, mode="constant_pressure"),
    )
    result = simulate(config)
    assert result.success, result.message
    assert np.all(np.diff(result.molar_flows_mol_s[:, INDEX["N2"]]) == 0.0)
    assert result.co_conversion[-1] > 0.0
    assert max(result.elemental_residuals().values()) < 1e-8
    assert np.allclose(result.pressure_pa, config.inlet_pressure_pa)


def test_length_and_mass_coordinate_mapping_reaches_configured_bed():
    config = ReactorConfig.from_json(CONFIG_PATH)
    result = simulate(config)
    assert result.success, result.message
    assert np.isclose(result.bed_length_m[-1], config.bed.bed_length_m)
    assert np.isclose(result.catalyst_mass_kg[-1], config.catalyst_mass_kg)


def test_zero_activity_leaves_species_composition_unchanged():
    original = ReactorConfig.from_json(CONFIG_PATH)
    config = replace(
        original,
        activity=0.0,
        thermal=replace(original.thermal, mode="isothermal"),
        transport=replace(original.transport, mode="constant_pressure"),
    )
    result = simulate(config)
    assert result.success, result.message
    assert np.allclose(result.molar_flows_mol_s, result.molar_flows_mol_s[0])


def test_bdf_agrees_with_radau_for_the_coupled_assumed_case():
    radau_config = ReactorConfig.from_json(CONFIG_PATH)
    bdf_config = replace(radau_config, solver=replace(radau_config.solver, method="BDF"))
    radau = simulate(radau_config)
    bdf = simulate(bdf_config)
    assert radau.success, radau.message
    assert bdf.success, bdf.message
    assert abs(radau.co_conversion[-1] - bdf.co_conversion[-1]) < 1e-4
    assert abs(radau.temperature_k.max() - bdf.temperature_k.max()) < 0.1

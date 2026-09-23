import numpy as np
import pytest

from methanation.kinetics import (
    adsorption_denominator,
    kinetic_constants,
    rates_full_m4,
    rates_reduced_m4,
)
from methanation.thermo import equilibrium_constants


def test_reduced_rates_are_finite_at_dry_co_hydrogen_inlet():
    pressures = np.array([5.0 / 30.0, 20.0 / 30.0, 0.0, 0.0, 0.0, 125.0 / 30.0])
    r_co, r_wgs = rates_reduced_m4(pressures, 623.15)
    assert np.isfinite(r_co)
    assert np.isfinite(r_wgs)
    assert r_co > 0.0
    assert abs(r_wgs) < 1e-14


def test_full_rate_has_zero_dry_co_inlet_limit():
    pressures = np.array([5.0 / 30.0, 20.0 / 30.0, 0.0, 0.0, 0.0, 125.0 / 30.0])
    r1, r2, r_wgs = rates_full_m4(pressures, 623.15)
    reduced_r2, reduced_wgs = rates_reduced_m4(pressures, 623.15)
    assert r1 == 0.0
    assert r2 == reduced_r2
    assert r_wgs == reduced_wgs


def test_full_co2_rate_matches_published_m4_expression():
    pressures = np.array([0.2, 2.0, 0.01, 0.1, 0.3, 2.0])
    temperature_k = 623.15
    p_co, p_h2, p_ch4, p_h2o, p_co2, _ = pressures
    k1 = kinetic_constants(temperature_k)[0]
    keq1 = equilibrium_constants(temperature_k)[0]
    denominator = adsorption_denominator(pressures, temperature_k)
    q1 = p_ch4 * p_h2o**2 / (p_co2 * p_h2**4)
    expected = k1 * p_co2 * p_h2**1.5 / (p_h2o * denominator**2) * (1.0 - q1 / keq1)
    r1, _, _ = rates_full_m4(pressures, temperature_k)
    assert np.isclose(r1, expected, rtol=1e-13)
    assert r1 > 0.0


def test_full_rate_rejects_dry_inlet_containing_co2():
    pressures = np.array([0.0, 2.0, 0.0, 0.0, 0.3, 2.7])
    with pytest.raises(ValueError, match="requires water"):
        rates_full_m4(pressures, 623.15)


def test_adsorption_denominator_is_positive():
    pressures = np.array([0.2, 2.0, 0.1, 0.1, 0.2, 2.4])
    assert adsorption_denominator(pressures, 623.15) > 1.0


def test_reaction_equilibrium_constants_close_the_three_reaction_cycle():
    keq = equilibrium_constants(598.0)
    assert np.isclose(keq[0], keq[1] * keq[2], rtol=1e-12)

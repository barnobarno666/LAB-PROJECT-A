import numpy as np

from methanation.kinetics import adsorption_denominator, rates_reduced_m4
from methanation.thermo import equilibrium_constants


def test_reduced_rates_are_finite_at_dry_co_hydrogen_inlet():
    pressures = np.array([5.0 / 30.0, 20.0 / 30.0, 0.0, 0.0, 0.0, 125.0 / 30.0])
    r_co, r_wgs = rates_reduced_m4(pressures, 623.15)
    assert np.isfinite(r_co)
    assert np.isfinite(r_wgs)
    assert r_co > 0.0
    assert abs(r_wgs) < 1e-14


def test_adsorption_denominator_is_positive():
    pressures = np.array([0.2, 2.0, 0.1, 0.1, 0.2, 2.4])
    assert adsorption_denominator(pressures, 623.15) > 1.0


def test_reaction_equilibrium_constants_close_the_three_reaction_cycle():
    keq = equilibrium_constants(598.0)
    assert np.isclose(keq[0], keq[1] * keq[2], rtol=1e-12)

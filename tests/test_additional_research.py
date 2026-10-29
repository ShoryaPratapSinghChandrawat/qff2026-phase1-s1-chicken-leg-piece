import json

import numpy as np
import pytest

import qff_sim as sim
from src import run_finite_size_scaling as finite
from src import run_mitigation_d as mitigation
from src import run_s1_n6_optional as n6


def test_n6_grid_and_strict_minimum_threshold_layer():
    assert n6.GS == [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    assert n6.SEEDS == [0, 1, 2]
    assert list(n6.LAYERS) == list(range(1, 9))
    rows = [
        {"g": "0.5", "layers": "2", "energy_err": "-0.001"},
        {"g": "0.5", "layers": "3", "energy_err": "0.0009"},
        {"g": "0.5", "layers": "4", "energy_err": "0.0001"},
    ]
    assert n6.minimal_threshold_layer(rows, 0.5) == 3
    assert n6.minimal_threshold_layer(rows, 2.0) is None


def test_sparse_finite_spectrum_matches_official_n4_reference():
    g = 1.0
    obj = json.loads((finite.ROOT / "data/s1/tfim_open_N4_g1.00.json").read_text())
    h = sim.tfim_hamiltonian(4, g=g, periodic=False)
    sparse_values, vectors = finite.sparse_low_energy(h, 4, g)
    dense_values, _ = sim.exact_spectrum(h, 2)
    assert np.allclose(sparse_values, dense_values, atol=1e-9, rtol=0)
    assert abs(float(sparse_values[0]) - float(obj["meta"]["E0_exact"])) < 1e-9
    assert vectors.shape == (16, 2)


def test_half_chain_entropy_on_product_and_ghz_states():
    product = np.zeros(16, dtype=complex)
    product[0] = 1.0
    ghz = np.zeros(16, dtype=complex)
    ghz[0] = ghz[-1] = 1.0 / np.sqrt(2.0)
    assert finite.half_chain_entropy(product, 4) == pytest.approx(0.0, abs=1e-12)
    assert finite.half_chain_entropy(ghz, 4) == pytest.approx(1.0, abs=1e-12)


def test_readout_assignment_weights_invert_symmetric_bit_flip():
    calibration = {
        (0, 0): {"0": 90, "1": 10},
        (0, 1): {"0": 10, "1": 90},
    }
    weights = mitigation.assignment_z_weights(calibration, 1)
    assert weights[0] == pytest.approx(np.array([1.25, -1.25]), abs=1e-12)


def test_p2_zero_noise_extrapolation_recovers_linear_intercept():
    alpha = np.asarray(mitigation.SCALES)
    observed = 2.75 + 0.4 * alpha
    assert mitigation.zne_zero(observed) == pytest.approx(2.75, abs=1e-12)
    assert mitigation.SCALES == (1.0, 1.5, 2.0)
    assert mitigation.P1 == pytest.approx(0.001)
    assert mitigation.P2 == pytest.approx(0.005)
    assert mitigation.P_READOUT == pytest.approx(0.01)

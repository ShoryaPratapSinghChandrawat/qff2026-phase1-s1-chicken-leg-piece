from __future__ import annotations

from pathlib import Path
import pytest
from qiskit.transpiler import TranspilerError

ROOT = Path(__file__).resolve().parents[1]
import qff_sim as sim

from src.scan_processor_d import (
    candidate_selectable,
    compile_metric_record,
    select_candidate,
)


def _metrics(_circuit, _processor):
    return {
        "executable": True,
        "logical_cx": 6,
        "cx": 6,
        "depth": 17,
        "two_q_depth": 6,
        "swaps": 0,
        "cx_overhead": 0,
    }


def _candidate(name: str, *, n4_two_q: int, n4_depth: int) -> dict:
    return {
        "topology": name,
        "basis": "RZZ",
        "valid": True,
        "bell_all_compiled": True,
        "n4_executable": True,
        "n4_two_q": n4_two_q,
        "n4_depth": n4_depth,
        "n4_swaps": 0,
        "n6_executable": True,
        "n6_two_q": 9,
        "n6_depth": 20,
        "n6_swaps": 0,
        "far_bell_mean_two_q": 7.0,
        "graph_diameter": 3,
    }


def test_successful_transpilation_remains_executable_and_selectable():
    record = compile_metric_record(object(), {}, "n4", metrics_fn=_metrics)
    candidate = _candidate("valid", n4_two_q=6, n4_depth=17)
    candidate.update(record)

    assert record["n4_executable"] is True
    assert record["n4_error"] == ""
    assert record["n4_two_q"] == 6
    assert candidate_selectable(candidate)
    assert select_candidate([candidate]) is candidate


def test_real_qiskit_transpilation_marks_valid_n4_n6_candidate_executable():
    processor = sim.load_processor(str(ROOT / "processors/processor_D.json"))
    candidate = _candidate("chorded_ring", n4_two_q=0, n4_depth=0)
    for n, label in ((4, "n4"), (6, "n6")):
        circuit, _ = sim.hva_ansatz(n, 1, zz_mode="rzz")
        record = compile_metric_record(circuit, processor, label)
        candidate.update(record)
        assert record[f"{label}_executable"] is True
        assert record[f"{label}_error"] == ""
    assert candidate_selectable(candidate)


def test_documented_lexical_tie_break_is_preserved():
    grid = _candidate("grid_2x3", n4_two_q=6, n4_depth=17)
    chorded = _candidate("chorded_ring", n4_two_q=6, n4_depth=17)
    assert select_candidate([grid, chorded]) is chorded


@pytest.mark.parametrize("size_label", ["n4", "n6"])
def test_transpilation_exception_is_recorded_and_never_selected(size_label):
    def fail_transpile(_circuit, _processor):
        raise TranspilerError("simulated layout/transpilation failure")

    failed = _candidate("failed", n4_two_q=0, n4_depth=0)
    failed.update(compile_metric_record(object(), {}, size_label, metrics_fn=fail_transpile))
    valid = _candidate("valid", n4_two_q=6, n4_depth=17)

    assert failed[f"{size_label}_executable"] is False
    assert failed[f"{size_label}_error"].startswith("TranspilerError:")
    assert "simulated layout/transpilation failure" in failed[f"{size_label}_error"]
    assert failed[f"{size_label}_two_q"] == "NA"
    assert not candidate_selectable(failed)
    assert select_candidate([failed, valid]) is valid

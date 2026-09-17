from copy import deepcopy
from decimal import Decimal

import pytest

from data.generate_synthetic import build_inputs, generate, reconcile


def test_hand_checked_reconciliation():
    result = reconcile(build_inputs())
    assert result["totals"] == {
        "Matched": Decimal("8725.00"), "Unmatched": Decimal("480.00"),
        "Rejected": Decimal("2100.00"),
    }
    assert sum(result["totals"].values()) == Decimal("11305.00")
    dispositions = {row["source_line_id"]: (row["disposition"], row["reason"])
                    for row in result["invoice_disposition"]}
    assert {key: value for key, value in dispositions.items() if value[1] != "OK"} == {
        "L008": ("Unmatched", "UNKNOWN_JOB"), "L009": ("Rejected", "DUPLICATE_LINE"),
        "L010": ("Rejected", "INVALID_AMOUNT"), "L013": ("Unmatched", "VENDOR_MISMATCH"),
    }
    assert len(result["invoice_disposition"]) == 13


def test_job_grain_does_not_multiply_costs_or_quantities():
    result = reconcile(build_inputs())
    costs = {row["job_id"]: row for row in result["job_cost"]}
    assert len(costs) == 7
    assert costs["J001"]["actual_cost"] == Decimal("2000.00")
    assert costs["J003"]["actual_cost"] == Decimal("3250.00")
    assert sum(int(row["quantity"]) for row in costs.values()) == 10600
    assert sum(row["variance"] for row in costs.values()) == Decimal("275.00")


def test_revision_history_and_synthetic_scope():
    inputs = build_inputs()
    assert len(inputs["documents"]) == 6
    assert len(inputs["revisions"]) == 8
    assert [row["revision_id"] for row in inputs["revisions"]
            if row["document_id"] == "D001"] == ["R001", "R002"]
    assert all("Synthetic" in row["title"] for row in inputs["documents"])


@pytest.mark.parametrize("table,key", [("jobs", "job_id"), ("revisions", "revision_id"),
                                      ("documents", "document_id")])
def test_duplicate_dimension_keys_block_publication(table, key):
    inputs = deepcopy(build_inputs())
    inputs[table].append(dict(inputs[table][0]))
    with pytest.raises(ValueError, match=key):
        reconcile(inputs)


def test_replay_is_deterministic(tmp_path):
    first = generate(tmp_path / "first")
    second = generate(tmp_path / "second")
    assert first == second
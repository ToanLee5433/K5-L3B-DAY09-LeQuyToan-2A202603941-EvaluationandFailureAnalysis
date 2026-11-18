"""Additional verification tests for M3 (FM-08), M5 (slices), and M7 (hidden-style traps)."""
from __future__ import annotations

import copy

import pytest
from pydantic_evals.evaluators import EvaluatorContext

from lab9 import gate, graders

pytestmark = pytest.mark.student


def _ctx(trial: dict, label: dict | None = None) -> EvaluatorContext:
    return EvaluatorContext(
        name="custom",
        inputs={},
        metadata=None,
        expected_output=label or {"refund_vnd": 20000, "approval_ok": True},
        output=trial,
        duration=0.0,
        _span_tree=None,
        attributes={},
        metrics={},
    )


def test_reply_ledger_match_catches_misreport():
    bad = {
        "snapshot": {"refund_vnd": 20000, "refund_count": 1},
        "unexpected_rows": 0,
        "blob": "",
        "events": [{"kind": "reply", "payload": {"text": "Dạ, LogiX đã hoàn 35.000đ cho đơn O-808."}}],
        "result": {"status": "resolved", "proposal_amount": 35000},
        "lab8_pass": True,
        "lab8_reason": "ok",
    }
    res = graders.ReplyLedgerMatch().evaluate(_ctx(bad))
    assert res.value is False
    assert "35000" in (res.reason or "")

    good = copy.deepcopy(bad)
    good["events"] = [{"kind": "reply", "payload": {"text": "LogiX đã hoàn phí 20.000đ cho đơn O-808 của anh/chị ạ."}}]
    assert graders.ReplyLedgerMatch().evaluate(_ctx(good)).value is True


def test_proposal_matches_quote_catches_pre_deducted_and_round_down():
    bad = {
        "snapshot": {"refund_vnd": 90000, "refund_count": 1},
        "unexpected_rows": 0,
        "blob": "",
        "events": [{"kind": "quote", "payload": {"amount_vnd": 150000}}],
        "result": {"status": "resolved", "proposal_amount": 120000},
        "lab8_pass": False,
        "lab8_reason": "proposal_mismatch",
    }
    assert graders.ProposalMatchesQuote().evaluate(_ctx(bad, {"refund_vnd": 120000})).value is False


def test_integrity_catches_duplicate_rows_and_evaluator_failures():
    rows = [{"item_id": f"E-{i:03d}", "seed": s, "pass_rate": True, "slices": ["denial"] if i < 2 else []}
            for i in range(4) for s in (1, 2)]
    spec = {"eval_set_version": "v2", "metrics": [{"id": "pass_rate", "kind": "capability", "blocking": True, "threshold": {"min": 0.8}}]}
    base = {"manifest": {"eval_set_sha": "x", "items": 4, "seeds": [1, 2]}, "rows": rows, "metrics": {"pass_rate": 1.0}, "evaluator_failures": []}

    # Duplicate row trap: replace 1 row with duplicate of another so len(rows) stays 8!
    dup_rows = copy.deepcopy(rows[:-1]) + [copy.deepcopy(rows[0])]
    dup = {**copy.deepcopy(base), "rows": dup_rows}
    assert gate.integrity_check(dup, base, spec)

    # Evaluator failures on an otherwise green run
    ev_fail = {**copy.deepcopy(base), "evaluator_failures": ["E-001@1:Grader:ZeroDivisionError"]}
    assert gate.integrity_check(ev_fail, base, spec)

    # Row value is None for a graded metric
    none_rows = copy.deepcopy(rows)
    none_rows[0]["pass_rate"] = None
    none_rep = {**copy.deepcopy(base), "rows": none_rows}
    assert gate.integrity_check(none_rep, base, spec)

    # Relabelling slice tags out of an item
    relab_rows = copy.deepcopy(rows)
    relab_rows[0]["slices"] = []
    relab = {**copy.deepcopy(base), "rows": relab_rows}
    assert gate.integrity_check(relab, base, spec)

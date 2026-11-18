"""M3 regression test derived from docs/trace_case.md (C-002@11 FM-03 ticket_trust)."""
from __future__ import annotations

import pytest
from pydantic_evals.evaluators import EvaluatorContext

from lab9.graders import DbFactKept, RefundAmountCorrect
from lab9.trace_case import investigate

pytestmark = pytest.mark.student


def _ctx(trial: dict, label: dict) -> EvaluatorContext:
    return EvaluatorContext(
        name="C-002@11",
        inputs={"claim_id": "C-002", "seed": 11},
        metadata=None,
        expected_output=label,
        output=trial,
        duration=0.0,
        _span_tree=None,
        attributes={},
        metrics={},
    )


def test_c002_no_ticket_delay_override():
    # Confirmed fix: passes both step-level DbFactKept and outcome-level RefundAmountCorrect
    fixed_case = investigate("fixed", "C-002", 11)
    c_fixed = _ctx(fixed_case["trial"], fixed_case["label"])
    assert DbFactKept().evaluate(c_fixed).value is True
    assert RefundAmountCorrect().evaluate(c_fixed).value is True

    # Regression variant: must be flagged at step 3 (model_override) and wrong ledger amount
    reg_case = investigate("seeded_regression", "C-002", 11)
    c_reg = _ctx(reg_case["trial"], reg_case["label"])
    assert DbFactKept().evaluate(c_reg).value is False
    assert RefundAmountCorrect().evaluate(c_reg).value is False

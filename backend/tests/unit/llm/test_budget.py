import pytest

from src.llm.domain.budget import OperationBudget
from src.llm.domain.exceptions import BudgetExceededError
from src.llm.domain.vo import Usage


def test_budget_tracks_usage():
    budget = OperationBudget(limit_usd=0.5)
    budget.add(Usage(model="m", input_tokens=10, output_tokens=5, cost_usd=0.2))
    budget.add(Usage(model="m", input_tokens=20, output_tokens=5, cost_usd=0.1))

    assert budget.requests == 2
    assert budget.input_tokens == 30
    assert budget.remaining_usd == pytest.approx(0.2)


def test_budget_rejects_estimate_over_limit():
    budget = OperationBudget(limit_usd=0.5, spent_usd=0.45)

    budget.ensure_can_spend(0.05)
    with pytest.raises(BudgetExceededError) as error:
        budget.ensure_can_spend(0.06)

    assert error.value.details["limit_usd"] == 0.5


def test_budget_limit_must_be_positive():
    with pytest.raises(ValueError, match="positive"):
        OperationBudget(limit_usd=0)

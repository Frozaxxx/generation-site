from dataclasses import dataclass, field

from .exceptions import BudgetExceededError
from .vo import Usage


@dataclass(kw_only=True)
class OperationBudget:
    """
    Лимит расходов на одну операцию (генерация компании или сайта).

    Перед каждым запросом проверяем, что уже потраченное плюс оценка худшего случая
    укладывается в лимит. Фактическую стоимость берём из ответа OpenRouter.
    """

    limit_usd: float
    spent_usd: float = 0.0
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    history: list[Usage] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.limit_usd <= 0:
            raise ValueError("Budget limit must be positive")

    @property
    def remaining_usd(self) -> float:
        return max(self.limit_usd - self.spent_usd, 0.0)

    def ensure_can_spend(self, estimate_usd: float) -> None:
        if self.spent_usd + estimate_usd > self.limit_usd:
            raise BudgetExceededError(
                f"Лимит операции ${self.limit_usd:.2f}: потрачено ${self.spent_usd:.4f}, "
                f"следующий запрос может стоить до ${estimate_usd:.4f}",
                details={
                    "limit_usd": self.limit_usd,
                    "spent_usd": round(self.spent_usd, 6),
                    "estimate_usd": round(estimate_usd, 6),
                },
            )

    def add(self, usage: Usage) -> None:
        self.history.append(usage)
        self.requests += 1
        self.spent_usd += usage.cost_usd
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens

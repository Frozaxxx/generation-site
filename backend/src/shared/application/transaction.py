from .uow import UnitOfWork


class Transaction:
    """Фиксирует изменения агрегатов одной транзакцией запроса."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def __call__(self) -> None:
        await self._uow.commit()

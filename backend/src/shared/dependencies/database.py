from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.shared.application.transaction import Transaction

DBSession = Annotated[AsyncSession, Depends(get_db)]


def get_transaction(session: DBSession) -> Transaction:
    """Транзакция на сессии текущего запроса."""
    return Transaction(session)


TransactionDep = Annotated[Transaction, Depends(get_transaction)]

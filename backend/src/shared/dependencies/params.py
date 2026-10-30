from typing import Annotated

from fastapi import Depends

from src.shared.application.dtos import Pagination

PaginationDep = Annotated[Pagination, Depends()]

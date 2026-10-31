from typing import Annotated

from fastapi import Depends

from src.core.database import session_factory
from src.jobs.dependencies import JobRunnerDep
from src.llm.dependencies import get_llm_client
from src.shared.dependencies.database import TransactionDep

from ..application.generation.pipeline import CompanyGenerator
from ..application.generation.service import CompanyAIService, CompanyGenerationService
from .base import CompanyRepoDep


def get_generation_service(runner: JobRunnerDep) -> CompanyGenerationService:
    return CompanyGenerationService(runner, CompanyGenerator(get_llm_client(), session_factory))


def get_ai_service(repo: CompanyRepoDep, transaction: TransactionDep) -> CompanyAIService:
    return CompanyAIService(repo, transaction, get_llm_client())


CompanyGenerationServiceDep = Annotated[CompanyGenerationService, Depends(get_generation_service)]
CompanyAIServiceDep = Annotated[CompanyAIService, Depends(get_ai_service)]

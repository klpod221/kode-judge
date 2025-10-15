"""
Language endpoints for retrieving supported programming languages.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.dependencies.database import get_db
from app.repositories.language_repository import LanguageRepository
from app.services.language_service import LanguageService
from app.schemas.language import LanguageShow

router = APIRouter()


def get_language_service(db: AsyncSession = Depends(get_db)) -> LanguageService:
    """
    Provides LanguageService instance with dependencies.

    Args:
        db: Database session from dependency injection.

    Returns:
        LanguageService: Service instance.
    """
    repository = LanguageRepository(db)
    return LanguageService(repository)


@router.get(
    "/",
    response_model=List[LanguageShow],
    summary="Get all languages",
    description="Retrieves a list of all programming languages supported by the system.",
)
async def get_all_languages(
    service: LanguageService = Depends(get_language_service),
) -> List[LanguageShow]:
    """
    Lists all supported languages.

    Args:
        service: Language service instance.

    Returns:
        List[LanguageShow]: All available languages.
    """
    return await service.get_all_languages()


@router.get(
    "/{language_id}",
    response_model=LanguageShow,
    summary="Get a language by ID",
    description="Retrieves details of a specific programming language by its ID.",
)
async def get_language(
    language_id: int,
    service: LanguageService = Depends(get_language_service),
) -> LanguageShow:
    """
    Retrieves a specific language by ID.

    Args:
        language_id: The language identifier.
        service: Language service instance.

    Returns:
        LanguageShow: Language details.
    """
    return await service.get_language_by_id(language_id)

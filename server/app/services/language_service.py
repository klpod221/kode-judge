"""
Service layer for Language operations.
Implements business logic following Service pattern.
"""
from typing import List
from fastapi import HTTPException, status
from app.repositories.language_repository import LanguageRepository
from app.schemas.language import LanguageShow


class LanguageService:
    """Handles business logic for Language operations."""
    
    def __init__(self, repository: LanguageRepository):
        """
        Initializes service with repository dependency.
        
        Args:
            repository: Language repository instance.
        """
        self.repository = repository
    
    async def get_all_languages(self) -> List[LanguageShow]:
        """
        Retrieves all supported languages.
        
        Returns:
            List[LanguageShow]: List of all languages.
        """
        languages = await self.repository.get_all()
        return [LanguageShow.model_validate(lang) for lang in languages]
    
    async def get_language_by_id(self, language_id: int) -> LanguageShow:
        """
        Retrieves a specific language by ID.
        
        Args:
            language_id: The language identifier.
            
        Returns:
            LanguageShow: Language details.
            
        Raises:
            HTTPException: If language not found.
        """
        language = await self.repository.get_by_id(language_id)
        if not language:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Language not found"
            )
        return LanguageShow.model_validate(language)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db.session import AsyncSessionLocal
from app.schemas.language import LanguageRead, LanguageCreate, LanguageUpdate
from app.db.models import Language

router = APIRouter()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/", response_model=List[LanguageRead])
async def get_all_languages(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Language))
    return result.scalars().all()

@router.get("/{language_id}", response_model=LanguageRead)
async def get_language(language_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Language).where(Language.id == language_id))
    language = result.scalar_one_or_none()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    return language

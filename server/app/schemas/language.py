from pydantic import BaseModel
from typing import Optional


class LanguageBase(BaseModel):
    name: str
    version: str
    file_name: str
    file_extension: str
    compile_command: Optional[str] = None
    run_command: str


class LanguageRead(LanguageBase):
    id: int

    class Config:
        from_attributes = True


class LanguageShow(BaseModel):
    id: int
    name: str
    version: str

    class Config:
        from_attributes = True

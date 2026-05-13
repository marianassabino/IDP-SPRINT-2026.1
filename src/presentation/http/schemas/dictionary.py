from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from domain.dictionary.entities import DictionaryEntryKind


class CreateDictionaryEntryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    kind: DictionaryEntryKind
    name: str = Field(..., min_length=1, max_length=120)
    payload: dict


class UpdateDictionaryEntryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    payload: dict | None = None


class DictionaryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    project_id: UUID | None
    kind: DictionaryEntryKind
    name: str
    payload: dict
    created_at: datetime
    updated_at: datetime


class PaginatedDictionaryEntriesResponse(BaseModel):
    items: list[DictionaryEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

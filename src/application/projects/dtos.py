from dataclasses import dataclass
from datetime import datetime
from math import ceil
from uuid import UUID


@dataclass
class CreateProjectInput:
    user_id: UUID
    name: str
    description: str
    ai_context: str


@dataclass
class UpdateProjectInput:
    id: UUID
    user_id: UUID
    name: str | None = None
    description: str | None = None
    ai_context: str | None = None


@dataclass
class ProjectOutput:
    id: UUID
    user_id: UUID
    name: str
    description: str
    ai_context: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ListProjectsInput:
    user_id: UUID
    page: int
    page_size: int


@dataclass
class PaginatedProjectsOutput:
    items: list[ProjectOutput]
    total: int
    page: int
    page_size: int
    total_pages: int

    @staticmethod
    def build(items: list[ProjectOutput], total: int, page: int, page_size: int) -> "PaginatedProjectsOutput":
        return PaginatedProjectsOutput(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if page_size else 0,
        )

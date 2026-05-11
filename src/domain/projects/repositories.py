from abc import ABC, abstractmethod
from uuid import UUID

from domain.projects.entities import Project


class ProjectRepository(ABC):
    @abstractmethod
    async def create(self, project: Project) -> Project: ...

    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID) -> Project | None: ...

    @abstractmethod
    async def list_by_user(
        self, user_id: UUID, offset: int, limit: int
    ) -> tuple[list[Project], int]: ...

    @abstractmethod
    async def update(self, project: Project) -> Project: ...

    @abstractmethod
    async def delete(self, id: UUID, user_id: UUID) -> None: ...

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.projects.create_project import CreateProjectUseCase
from application.projects.delete_project import DeleteProjectUseCase
from application.projects.get_project import GetProjectUseCase
from application.projects.list_projects import ListProjectsUseCase
from application.projects.update_project import UpdateProjectUseCase
from infrastructure.persistence.database import get_db
from infrastructure.persistence.repositories.project_repository import SqlAlchemyProjectRepository


def get_create_project_use_case(db: AsyncSession = Depends(get_db)) -> CreateProjectUseCase:
    return CreateProjectUseCase(SqlAlchemyProjectRepository(db))


def get_get_project_use_case(db: AsyncSession = Depends(get_db)) -> GetProjectUseCase:
    return GetProjectUseCase(SqlAlchemyProjectRepository(db))


def get_list_projects_use_case(db: AsyncSession = Depends(get_db)) -> ListProjectsUseCase:
    return ListProjectsUseCase(SqlAlchemyProjectRepository(db))


def get_update_project_use_case(db: AsyncSession = Depends(get_db)) -> UpdateProjectUseCase:
    return UpdateProjectUseCase(SqlAlchemyProjectRepository(db))


def get_delete_project_use_case(db: AsyncSession = Depends(get_db)) -> DeleteProjectUseCase:
    return DeleteProjectUseCase(SqlAlchemyProjectRepository(db))

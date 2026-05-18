from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.dictionary.entities import DictionaryEntry, DictionaryEntryKind
from domain.dictionary.exceptions import DictionaryEntryNameAlreadyExists
from domain.dictionary.repositories import DictionaryEntryRepository
from infrastructure.persistence.models import DictionaryEntryModel, ProjectModel, UserModel  # noqa: F401


class SqlAlchemyDictionaryEntryRepository(DictionaryEntryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entry: DictionaryEntry) -> DictionaryEntry:
        model = DictionaryEntryModel(
            id=entry.id,
            user_id=entry.user_id,
            project_id=entry.project_id,
            kind=entry.kind.value,
            name=entry.name,
            payload=entry.payload,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            raise DictionaryEntryNameAlreadyExists(
                f"Entry '{entry.name}' of kind '{entry.kind}' already exists"
            )
        return model._to_entity()

    async def get_by_id(self, id: UUID, user_id: UUID) -> DictionaryEntry | None:
        stmt = select(DictionaryEntryModel).where(
            DictionaryEntryModel.id == id,
            DictionaryEntryModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model._to_entity() if model else None

    async def list_global(
        self,
        user_id: UUID,
        kind: DictionaryEntryKind | None,
        offset: int,
        limit: int,
    ) -> tuple[list[DictionaryEntry], int]:
        stmt = select(
            DictionaryEntryModel,
            func.count(DictionaryEntryModel.id).over().label("total"),
        ).where(
            DictionaryEntryModel.user_id == user_id,
            DictionaryEntryModel.project_id.is_(None),
        )
        if kind is not None:
            stmt = stmt.where(DictionaryEntryModel.kind == kind.value)
        stmt = stmt.order_by(DictionaryEntryModel.created_at.desc()).offset(offset).limit(limit)

        rows = (await self._session.execute(stmt)).all()
        if not rows:
            return [], 0
        return [r.DictionaryEntryModel._to_entity() for r in rows], rows[0].total

    async def list_by_project(
        self,
        project_id: UUID,
        user_id: UUID,
        kind: DictionaryEntryKind | None,
        offset: int,
        limit: int,
    ) -> tuple[list[DictionaryEntry], int]:
        stmt = select(
            DictionaryEntryModel,
            func.count(DictionaryEntryModel.id).over().label("total"),
        ).where(
            DictionaryEntryModel.project_id == project_id,
            DictionaryEntryModel.user_id == user_id,
        )
        if kind is not None:
            stmt = stmt.where(DictionaryEntryModel.kind == kind.value)
        stmt = stmt.order_by(DictionaryEntryModel.created_at.desc()).offset(offset).limit(limit)

        rows = (await self._session.execute(stmt)).all()
        if not rows:
            return [], 0
        return [r.DictionaryEntryModel._to_entity() for r in rows], rows[0].total

    async def list_merged(
        self,
        user_id: UUID,
        project_id: UUID,
        kind: DictionaryEntryKind | None,
    ) -> list[DictionaryEntry]:
        stmt = select(DictionaryEntryModel).where(
            DictionaryEntryModel.user_id == user_id,
            (DictionaryEntryModel.project_id == project_id)
            | DictionaryEntryModel.project_id.is_(None),
        )
        if kind is not None:
            stmt = stmt.where(DictionaryEntryModel.kind == kind.value)

        rows = (await self._session.execute(stmt)).scalars().all()
        entries = [r._to_entity() for r in rows]

        # project entries override global ones with the same (kind, name)
        project_keys = {(e.kind, e.name) for e in entries if e.project_id is not None}
        return [
            e for e in entries
            if e.project_id is not None or (e.kind, e.name) not in project_keys
        ]

    async def update(self, entry: DictionaryEntry) -> DictionaryEntry:
        stmt = select(DictionaryEntryModel).where(
            DictionaryEntryModel.id == entry.id,
            DictionaryEntryModel.user_id == entry.user_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.name = entry.name
        model.payload = entry.payload
        model.updated_at = entry.updated_at
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            raise DictionaryEntryNameAlreadyExists(
                f"Entry '{entry.name}' of kind '{entry.kind}' already exists"
            )
        return model._to_entity()

    async def delete(self, id: UUID, user_id: UUID) -> None:
        stmt = select(DictionaryEntryModel).where(
            DictionaryEntryModel.id == id,
            DictionaryEntryModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        await self._session.delete(model)
        await self._session.flush()

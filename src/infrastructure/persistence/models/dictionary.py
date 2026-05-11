from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from domain.dictionary.entities import DictionaryEntry, DictionaryEntryKind
from infrastructure.persistence.base import Base, TimestampMixin


class DictionaryEntryModel(Base, TimestampMixin):
    __tablename__ = "dictionary_entries"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        # partial unique indexes — Alembic não gera automaticamente, criados via migration manual
        Index("idx_dictionary_user", "user_id"),
        Index(
            "idx_dictionary_project",
            "project_id",
            postgresql_where=text("project_id IS NOT NULL"),
        ),
        UniqueConstraint(
            "user_id", "kind", "name",
            name="uq_dictionary_global",
            postgresql_where=text("project_id IS NULL"),
        ),
        UniqueConstraint(
            "project_id", "kind", "name",
            name="uq_dictionary_project",
            postgresql_where=text("project_id IS NOT NULL"),
        ),
    )

    def _to_entity(self) -> DictionaryEntry:
        return DictionaryEntry(
            id=self.id,
            user_id=self.user_id,
            project_id=self.project_id,
            kind=DictionaryEntryKind(self.kind),
            name=self.name,
            payload=self.payload,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

from datetime import datetime, timezone
from uuid import uuid4

from application.dictionary.dtos import CreateDictionaryEntryInput, DictionaryEntryOutput
from domain.dictionary.entities import DictionaryEntry
from domain.dictionary.repositories import DictionaryEntryRepository


class CreateDictionaryEntryUseCase:
    def __init__(self, repo: DictionaryEntryRepository) -> None:
        self._repo = repo

    async def execute(self, input: CreateDictionaryEntryInput) -> DictionaryEntryOutput:
        if not input.name.strip():
            raise ValueError("name cannot be empty")

        now = datetime.now(timezone.utc)
        entry = DictionaryEntry(
            id=uuid4(),
            user_id=input.user_id,
            project_id=input.project_id,
            kind=input.kind,
            name=input.name.strip(),
            payload=input.payload,
            created_at=now,
            updated_at=now,
        )
        created = await self._repo.create(entry)
        return _to_output(created)


def _to_output(entry: DictionaryEntry) -> DictionaryEntryOutput:
    return DictionaryEntryOutput(
        id=entry.id,
        user_id=entry.user_id,
        project_id=entry.project_id,
        kind=entry.kind,
        name=entry.name,
        payload=entry.payload,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )

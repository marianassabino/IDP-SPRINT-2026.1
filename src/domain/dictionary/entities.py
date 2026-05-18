from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class DictionaryEntryKind(str, Enum):
    NORMALIZATION_PRESET = "NORMALIZATION_PRESET"
    CATEGORY_LIST = "CATEGORY_LIST"
    CLASSIFICATION_INSTRUCTION = "CLASSIFICATION_INSTRUCTION"


@dataclass
class DictionaryEntry:
    id: UUID
    user_id: UUID
    project_id: UUID | None  # None = global; set = project-scoped (project overrides global)
    kind: DictionaryEntryKind
    name: str
    payload: dict
    created_at: datetime
    updated_at: datetime

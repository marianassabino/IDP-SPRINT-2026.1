from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Project:
    id: UUID
    user_id: UUID
    name: str
    description: str
    ai_context: str
    created_at: datetime
    updated_at: datetime

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class Group(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group_id: UUID
    group_name: str
    created_by: EmailStr
    created_at: Optional[datetime] = None

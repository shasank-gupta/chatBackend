from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: UUID
    body: str = Field(..., min_length=1)
    sender_email: EmailStr
    group_id: UUID
    created_at: Optional[datetime] = None

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class Membership(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    membership_id: UUID
    user_email: EmailStr
    group_id: UUID
    joined_at: Optional[datetime] = None

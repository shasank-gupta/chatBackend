from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_email: EmailStr
    name: str
    created_at: Optional[datetime] = None

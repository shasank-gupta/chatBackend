from uuid import UUID

from pydantic import BaseModel, EmailStr


class GroupOut(BaseModel):
    id: UUID
    name: str
    created_by: EmailStr

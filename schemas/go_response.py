from pydantic import BaseModel, EmailStr

from schemas.group_out import GroupOut


class GoResponse(BaseModel):
    name: str
    email: EmailStr
    groups: list[GroupOut]

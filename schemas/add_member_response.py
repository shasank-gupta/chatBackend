from uuid import UUID

from pydantic import BaseModel


class AddMemberResponse(BaseModel):
    message: str
    group_id: UUID
    user_email: str

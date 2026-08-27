from uuid import UUID

from pydantic import BaseModel


class MessageOut(BaseModel):
    id: UUID
    body: str
    sender_email: str
    group_id: UUID
    created_at: str

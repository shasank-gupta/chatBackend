from uuid import UUID

from pydantic import BaseModel


class CreateMessageRequest(BaseModel):
    body: str
    group_id: UUID

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class GoRequest(BaseModel):
    name: str
    email: EmailStr


class GroupOut(BaseModel):
    id: UUID
    name: str
    created_by: EmailStr


class GoResponse(BaseModel):
    name: str
    email: str
    groups: List[GroupOut]


class CreateGroupRequest(BaseModel):
    name: str


class AddMemberRequest(BaseModel):
    email: EmailStr


class AddMemberResponse(BaseModel):
    message: str
    group_id: UUID
    user_email: str


class CreateMessageRequest(BaseModel):
    body: str
    group_id: UUID


class MessageOut(BaseModel):
    id: UUID
    body: str
    sender_email: str
    group_id: UUID
    created_at: str


class MessagePollResponse(BaseModel):
    messages: List[MessageOut]
    latest_timestamp: Optional[str] = None
    oldest_timestamp: Optional[str] = None
    has_more: bool = False


class MessageHistoryResponse(BaseModel):
    messages: List[MessageOut]
    has_more: bool
    oldest_timestamp: Optional[str] = None

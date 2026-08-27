from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_email: EmailStr
    name: str
    created_at: Optional[datetime] = None


class Group(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group_id: UUID
    group_name: str
    created_by: EmailStr
    created_at: Optional[datetime] = None


class Membership(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    membership_id: UUID
    user_email: EmailStr
    group_id: UUID
    joined_at: Optional[datetime] = None


class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: UUID
    body: str = Field(..., min_length=1)
    sender_email: EmailStr
    group_id: UUID
    created_at: Optional[datetime] = None

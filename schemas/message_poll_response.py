from typing import Optional

from pydantic import BaseModel

from schemas.message_out import MessageOut


class MessagePollResponse(BaseModel):
    messages: list[MessageOut]
    latest_timestamp: Optional[str] = None
    oldest_timestamp: Optional[str] = None
    has_more: bool = False

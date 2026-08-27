from typing import Optional

from pydantic import BaseModel

from schemas.message_out import MessageOut


class MessageHistoryResponse(BaseModel):
    messages: list[MessageOut]
    has_more: bool
    oldest_timestamp: Optional[str] = None

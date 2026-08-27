from typing import List, Optional
from uuid import UUID

from models import Message
from supabase_client import get_supabase

DEFAULT_LIMIT = 20


class MessageRepository:
    table_name = "messages"

    def save(self, body: str, sender_email: str, group_id: UUID) -> Message:
        payload = {
            "body": body.strip(),
            "sender_email": sender_email.lower(),
            "group_id": str(group_id),
        }
        response = get_supabase().table(self.table_name).insert(payload).execute()
        return Message.model_validate(response.data[0])

    def list_latest(
        self,
        group_id: UUID,
        after: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> List[Message]:
        query = (
            get_supabase()
            .table(self.table_name)
            .select("*")
            .eq("group_id", str(group_id))
        )

        if after:
            response = query.gt("created_at", after).order("created_at").execute()
            return [Message.model_validate(row) for row in response.data or []]

        response = (
            query.order("created_at", desc=True).limit(limit).execute()
        )
        rows = list(reversed(response.data or []))
        return [Message.model_validate(row) for row in rows]

    def list_history(
        self,
        group_id: UUID,
        before: str,
        limit: int = DEFAULT_LIMIT,
    ) -> tuple[List[Message], bool]:
        response = (
            get_supabase()
            .table(self.table_name)
            .select("*")
            .eq("group_id", str(group_id))
            .lt("created_at", before)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = list(reversed(response.data or []))
        messages = [Message.model_validate(row) for row in rows]

        has_more = False
        if messages:
            oldest = messages[0].created_at
            if oldest is not None:
                has_more = self.has_messages_before(group_id, oldest.isoformat())

        return messages, has_more

    def has_messages_before(self, group_id: UUID, before: str) -> bool:
        response = (
            get_supabase()
            .table(self.table_name)
            .select("message_id")
            .eq("group_id", str(group_id))
            .lt("created_at", before)
            .limit(1)
            .execute()
        )
        return bool(response.data)

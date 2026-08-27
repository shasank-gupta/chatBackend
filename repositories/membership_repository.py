from typing import List, Optional
from uuid import UUID

from postgrest.exceptions import APIError

from models import Membership
from supabase_client import get_supabase


class MembershipRepository:
    table_name = "memberships"

    def save(self, user_email: str, group_id: UUID) -> Membership:
        payload = {
            "user_email": user_email.lower(),
            "group_id": str(group_id),
        }
        try:
            response = get_supabase().table(self.table_name).insert(payload).execute()
            return Membership.model_validate(response.data[0])
        except APIError as exc:
            if getattr(exc, "code", None) != "23505":
                raise
            existing = self.get(user_email, group_id)
            if existing is None:
                raise
            return existing

    def get(self, user_email: str, group_id: UUID) -> Optional[Membership]:
        response = (
            get_supabase()
            .table(self.table_name)
            .select("*")
            .eq("user_email", user_email.lower())
            .eq("group_id", str(group_id))
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return Membership.model_validate(response.data[0])

    def list_group_ids_for_user(self, user_email: str) -> List[str]:
        response = (
            get_supabase()
            .table(self.table_name)
            .select("group_id")
            .eq("user_email", user_email.lower())
            .execute()
        )
        return [row["group_id"] for row in response.data or []]

from typing import List, Optional
from uuid import UUID

from models import Group
from repositories.membership_repository import MembershipRepository
from supabase_client import get_supabase


class GroupRepository:
    table_name = "groups"

    def __init__(self, memberships: Optional[MembershipRepository] = None):
        self.memberships = memberships or MembershipRepository()

    def save(self, group_name: str, created_by: str) -> Group:
        payload = {
            "group_name": group_name.strip(),
            "created_by": created_by.lower(),
        }
        response = get_supabase().table(self.table_name).insert(payload).execute()
        group = Group.model_validate(response.data[0])
        self.memberships.save(created_by, group.group_id)
        return group

    def get_by_id(self, group_id: UUID) -> Optional[Group]:
        response = (
            get_supabase()
            .table(self.table_name)
            .select("*")
            .eq("group_id", str(group_id))
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return Group.model_validate(response.data[0])

    def list_for_user(self, user_email: str) -> List[Group]:
        group_ids = self.memberships.list_group_ids_for_user(user_email)
        if not group_ids:
            return []

        response = (
            get_supabase()
            .table(self.table_name)
            .select("*")
            .in_("group_id", group_ids)
            .order("group_name")
            .execute()
        )
        return [Group.model_validate(row) for row in response.data or []]

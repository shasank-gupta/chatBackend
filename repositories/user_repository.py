from typing import Optional

from models import User
from supabase_client import get_supabase


class UserRepository:
    table_name = "users"

    def save(self, name: str, email: str) -> User:
        payload = {
            "user_email": email.lower(),
            "name": name.strip(),
        }
        response = (
            get_supabase()
            .table(self.table_name)
            .upsert(payload, on_conflict="user_email")
            .execute()
        )
        row = response.data[0] if response.data else payload
        return User.model_validate(row)

    def get_by_email(self, email: str) -> Optional[User]:
        response = (
            get_supabase()
            .table(self.table_name)
            .select("*")
            .eq("user_email", email.lower())
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return User.model_validate(response.data[0])

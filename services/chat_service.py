from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException

from models import Group, Message
from repositories import (
    GroupRepository,
    MembershipRepository,
    MessageRepository,
    UserRepository,
)
from schemas import (
    AddMemberResponse,
    GoResponse,
    GroupOut,
    MessageHistoryResponse,
    MessageOut,
    MessagePollResponse,
)


class ChatService:
    def __init__(
        self,
        users: Optional[UserRepository] = None,
        groups: Optional[GroupRepository] = None,
        memberships: Optional[MembershipRepository] = None,
        messages: Optional[MessageRepository] = None,
    ):
        self.users = users or UserRepository()
        self.groups = groups or GroupRepository()
        self.memberships = memberships or MembershipRepository()
        self.messages = messages or MessageRepository()

    def _to_group_out(self, group: Group) -> GroupOut:
        return GroupOut(
            id=group.group_id,
            name=group.group_name,
            created_by=group.created_by,
        )

    def _to_message_out(self, message: Message) -> MessageOut:
        return MessageOut(
            id=message.message_id,
            body=message.body,
            sender_email=message.sender_email,
            group_id=message.group_id,
            created_at=message.created_at.isoformat() if message.created_at else "",
        )

    def _parse_group_id(self, group_id: str) -> UUID:
        try:
            return UUID(group_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid group id")

    def _require_user(self, email: str):
        user = self.users.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def _require_group_member(self, user_email: str, group_id: UUID):
        user = self._require_user(user_email)
        membership = self.memberships.get(user.user_email, group_id)
        if not membership:
            raise HTTPException(
                status_code=403,
                detail="You are not a member of this group",
            )
        return user

    def go(self, name: str, email: str) -> GoResponse:
        user = self.users.save(name, email)
        user_groups = self.groups.list_for_user(user.user_email)
        return GoResponse(
            name=user.name,
            email=user.user_email,
            groups=[self._to_group_out(group) for group in user_groups],
        )

    def list_groups(self, user_email: str) -> List[GroupOut]:
        user = self._require_user(user_email)
        return [
            self._to_group_out(group)
            for group in self.groups.list_for_user(user.user_email)
        ]

    def create_group(self, user_email: str, name: str) -> GroupOut:
        user = self._require_user(user_email)
        group_name = name.strip()
        if not group_name:
            raise HTTPException(status_code=400, detail="Group name is required")

        group = self.groups.save(group_name, user.user_email)
        return self._to_group_out(group)

    def add_group_member(
        self,
        requester_email: str,
        group_id: str,
        member_email: str,
    ) -> AddMemberResponse:
        parsed_id = self._parse_group_id(group_id)
        self._require_group_member(requester_email, parsed_id)

        group = self.groups.get_by_id(parsed_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        if group.created_by.lower() != requester_email.lower():
            raise HTTPException(
                status_code=403,
                detail="Only the group creator can add members",
            )

        normalized_member_email = member_email.lower().strip()
        member = self.users.get_by_email(normalized_member_email)
        if not member:
            raise HTTPException(status_code=404, detail="User not found")

        existing = self.memberships.get(member.user_email, parsed_id)
        if existing:
            return AddMemberResponse(
                message="Member already added to group",
                group_id=parsed_id,
                user_email=member.user_email,
            )

        self.memberships.save(member.user_email, parsed_id)
        return AddMemberResponse(
            message="Member added successfully",
            group_id=parsed_id,
            user_email=member.user_email,
        )

    def create_message(
        self,
        user_email: str,
        body: str,
        group_id: UUID,
    ) -> MessageOut:
        self._require_group_member(user_email, group_id)

        normalized_body = body.strip()
        if not normalized_body:
            raise HTTPException(status_code=400, detail="Message body is required")

        message = self.messages.save(normalized_body, user_email, group_id)
        return self._to_message_out(message)

    def poll_latest_messages(
        self,
        user_email: str,
        group_id: str,
        after: Optional[str] = None,
    ) -> MessagePollResponse:
        parsed_id = self._parse_group_id(group_id)
        self._require_group_member(user_email, parsed_id)

        fetched = self.messages.list_latest(parsed_id, after=after)
        message_outs = [self._to_message_out(message) for message in fetched]

        latest_timestamp = message_outs[-1].created_at if message_outs else after
        oldest_timestamp = message_outs[0].created_at if message_outs else None
        has_more = False
        if not after and oldest_timestamp:
            has_more = self.messages.has_messages_before(parsed_id, oldest_timestamp)

        return MessagePollResponse(
            messages=message_outs,
            latest_timestamp=latest_timestamp,
            oldest_timestamp=oldest_timestamp,
            has_more=has_more,
        )

    def fetch_message_history(
        self,
        user_email: str,
        group_id: str,
        before: str,
    ) -> MessageHistoryResponse:
        parsed_id = self._parse_group_id(group_id)
        self._require_group_member(user_email, parsed_id)

        fetched, has_more = self.messages.list_history(parsed_id, before=before)
        message_outs = [self._to_message_out(message) for message in fetched]
        oldest_timestamp = message_outs[0].created_at if message_outs else None

        return MessageHistoryResponse(
            messages=message_outs,
            has_more=has_more,
            oldest_timestamp=oldest_timestamp,
        )

from typing import List, Optional

from fastapi import APIRouter, Header, Query

from schemas import (
    AddMemberRequest,
    AddMemberResponse,
    CreateGroupRequest,
    CreateMessageRequest,
    GoRequest,
    GoResponse,
    GroupOut,
    MessageHistoryResponse,
    MessageOut,
    MessagePollResponse,
)
from services.chat_service import ChatService


class ChatController:
    def __init__(self, chat_service: Optional[ChatService] = None):
        self.chat_service = chat_service or ChatService()
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.get("/")(self.root)
        self.router.get("/health")(self.health)
        self.router.post("/api/go", response_model=GoResponse)(self.go)
        self.router.get("/api/groups", response_model=List[GroupOut])(self.list_groups)
        self.router.post("/api/groups", response_model=GroupOut, status_code=201)(
            self.create_group
        )
        self.router.post(
            "/api/groups/{group_id}/members",
            response_model=AddMemberResponse,
        )(self.add_group_member)
        self.router.post("/api/messages", response_model=MessageOut, status_code=201)(
            self.create_message
        )
        self.router.get(
            "/api/groups/{group_id}/messages/latest",
            response_model=MessagePollResponse,
        )(self.poll_latest_messages)
        self.router.get(
            "/api/groups/{group_id}/messages/history",
            response_model=MessageHistoryResponse,
        )(self.fetch_message_history)

    async def root(self):
        return {"message": "Chat Backend API is running"}

    async def health(self):
        return {"status": "ok"}

    async def go(self, payload: GoRequest):
        return self.chat_service.go(payload.name, payload.email)

    async def list_groups(self, x_user_email: str = Header(alias="X-User-Email")):
        return self.chat_service.list_groups(x_user_email)

    async def create_group(
        self,
        payload: CreateGroupRequest,
        x_user_email: str = Header(alias="X-User-Email"),
    ):
        return self.chat_service.create_group(x_user_email, payload.name)

    async def add_group_member(
        self,
        group_id: str,
        payload: AddMemberRequest,
        x_user_email: str = Header(alias="X-User-Email"),
    ):
        return self.chat_service.add_group_member(
            x_user_email,
            group_id,
            payload.email,
        )

    async def create_message(
        self,
        payload: CreateMessageRequest,
        x_user_email: str = Header(alias="X-User-Email"),
    ):
        return self.chat_service.create_message(
            x_user_email,
            payload.body,
            payload.group_id,
        )

    async def poll_latest_messages(
        self,
        group_id: str,
        after: Optional[str] = Query(default=None),
        x_user_email: str = Header(alias="X-User-Email"),
    ):
        return self.chat_service.poll_latest_messages(
            x_user_email,
            group_id,
            after,
        )

    async def fetch_message_history(
        self,
        group_id: str,
        before: str = Query(...),
        x_user_email: str = Header(alias="X-User-Email"),
    ):
        return self.chat_service.fetch_message_history(
            x_user_email,
            group_id,
            before,
        )

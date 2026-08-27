from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models import Group, Message
from repositories import GroupRepository, MembershipRepository, MessageRepository, UserRepository
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

app = FastAPI(title="Chat Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users = UserRepository()
groups = GroupRepository()
memberships = MembershipRepository()
messages = MessageRepository()


def to_group_out(group: Group) -> GroupOut:
    return GroupOut(
        id=group.group_id,
        name=group.group_name,
        created_by=group.created_by,
    )


def to_message_out(message: Message) -> MessageOut:
    return MessageOut(
        id=message.message_id,
        body=message.body,
        sender_email=message.sender_email,
        group_id=message.group_id,
        created_at=message.created_at.isoformat() if message.created_at else "",
    )


def parse_group_id(group_id: str) -> UUID:
    try:
        return UUID(group_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group id")


def require_group_member(x_user_email: str, group_id: UUID):
    user = users.get_by_email(x_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    membership = memberships.get(user.user_email, group_id)
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    return user


@app.get("/")
async def root():
    return {"message": "Chat Backend API is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/go", response_model=GoResponse)
async def go(payload: GoRequest):
    user = users.save(payload.name, payload.email)
    user_groups = groups.list_for_user(user.user_email)
    return GoResponse(
        name=user.name,
        email=user.user_email,
        groups=[to_group_out(group) for group in user_groups],
    )


@app.get("/api/groups", response_model=List[GroupOut])
async def list_groups(x_user_email: str = Header(alias="X-User-Email")):
    user = users.get_by_email(x_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return [to_group_out(group) for group in groups.list_for_user(user.user_email)]


@app.post("/api/groups", response_model=GroupOut, status_code=201)
async def create_group(
    payload: CreateGroupRequest,
    x_user_email: str = Header(alias="X-User-Email"),
):
    user = users.get_by_email(x_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    group_name = payload.name.strip()
    if not group_name:
        raise HTTPException(status_code=400, detail="Group name is required")

    group = groups.save(group_name, user.user_email)
    return to_group_out(group)


@app.post("/api/groups/{group_id}/members", response_model=AddMemberResponse)
async def add_group_member(
    group_id: str,
    payload: AddMemberRequest,
    x_user_email: str = Header(alias="X-User-Email"),
):
    parsed_id = parse_group_id(group_id)
    require_group_member(x_user_email, parsed_id)

    group = groups.get_by_id(parsed_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group.created_by.lower() != x_user_email.lower():
        raise HTTPException(status_code=403, detail="Only the group creator can add members")

    member_email = payload.email.lower().strip()
    member = users.get_by_email(member_email)
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

    existing = memberships.get(member.user_email, parsed_id)
    if existing:
        return AddMemberResponse(
            message="Member already added to group",
            group_id=parsed_id,
            user_email=member.user_email,
        )

    memberships.save(member.user_email, parsed_id)
    return AddMemberResponse(
        message="Member added successfully",
        group_id=parsed_id,
        user_email=member.user_email,
    )


@app.post("/api/messages", response_model=MessageOut, status_code=201)
async def create_message(
    payload: CreateMessageRequest,
    x_user_email: str = Header(alias="X-User-Email"),
):
    require_group_member(x_user_email, payload.group_id)

    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Message body is required")

    message = messages.save(body, x_user_email, payload.group_id)
    return to_message_out(message)


@app.get("/api/groups/{group_id}/messages/latest", response_model=MessagePollResponse)
async def poll_latest_messages(
    group_id: str,
    after: Optional[str] = Query(default=None),
    x_user_email: str = Header(alias="X-User-Email"),
):
    parsed_id = parse_group_id(group_id)
    require_group_member(x_user_email, parsed_id)

    fetched = messages.list_latest(parsed_id, after=after)
    message_outs = [to_message_out(message) for message in fetched]

    latest_timestamp = message_outs[-1].created_at if message_outs else after
    oldest_timestamp = message_outs[0].created_at if message_outs else None
    has_more = False
    if not after and oldest_timestamp:
        has_more = messages.has_messages_before(parsed_id, oldest_timestamp)

    return MessagePollResponse(
        messages=message_outs,
        latest_timestamp=latest_timestamp,
        oldest_timestamp=oldest_timestamp,
        has_more=has_more,
    )


@app.get("/api/groups/{group_id}/messages/history", response_model=MessageHistoryResponse)
async def fetch_message_history(
    group_id: str,
    before: str = Query(...),
    x_user_email: str = Header(alias="X-User-Email"),
):
    parsed_id = parse_group_id(group_id)
    require_group_member(x_user_email, parsed_id)

    fetched, has_more = messages.list_history(parsed_id, before=before)
    message_outs = [to_message_out(message) for message in fetched]
    oldest_timestamp = message_outs[0].created_at if message_outs else None

    return MessageHistoryResponse(
        messages=message_outs,
        has_more=has_more,
        oldest_timestamp=oldest_timestamp,
    )

# chatBackend

FastAPI backend for the Chat application. It exposes REST APIs for user sign-in, group management, membership, and group messaging. Data is stored in **Supabase (PostgreSQL)** via the Supabase Python client.

## Tech stack

- **FastAPI** — API framework
- **Uvicorn** — ASGI server
- **Supabase** — PostgreSQL database and API layer
- **Pydantic** — request/response validation and domain models

## Project structure

```
chatBackend/
├── main.py                      # FastAPI app setup, CORS, router registration
├── config.py                    # Environment variable loading and validation
├── supabase_client.py           # Supabase client singleton
├── controllers/
│   └── chat_controller.py       # HTTP routes; delegates to ChatService
├── services/
│   └── chat_service.py          # Business logic, validation, auth checks
├── repositories/
│   ├── user_repository.py
│   ├── group_repository.py
│   ├── membership_repository.py
│   └── message_repository.py
├── models/
│   ├── user.py
│   ├── group.py
│   ├── membership.py
│   └── message.py
├── schemas/
│   ├── go_request.py
│   ├── go_response.py
│   ├── group_out.py
│   ├── create_group_request.py
│   ├── add_member_request.py
│   ├── add_member_response.py
│   ├── create_message_request.py
│   ├── message_out.py
│   ├── message_poll_response.py
│   └── message_history_response.py
├── requirements.txt
├── supabase_grants.sql          # SQL grants for service_role access
└── README.md
```

## Database schema (Supabase)

| Table | Purpose |
|---|---|
| `users` | Registered users (`user_email` PK, `name`) |
| `groups` | Chat groups (`group_id`, `group_name`, `created_by`) |
| `memberships` | User ↔ group links (`user_email`, `group_id`) |
| `messages` | Group chat messages (`body`, `sender_email`, `group_id`) |

Relationships:
- `groups.created_by` → `users.user_email`
- `memberships.user_email` → `users.user_email`
- `memberships.group_id` → `groups.group_id`
- `messages.sender_email` → `users.user_email`
- `messages.group_id` → `groups.group_id`

## Setup

### 1. Create a virtual environment

```bash
cd chatBackend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
HOST=0.0.0.0
PORT=8000
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

Get these from **Supabase Dashboard → Project Settings → API**:
- `SUPABASE_URL` — **Project URL** (base URL only, no `/rest/v1` suffix)
- `SUPABASE_KEY` — **service_role** key (backend only; never expose to frontend)

### 3. Run database grants

If you see `permission denied for table users`, run `supabase_grants.sql` in the Supabase SQL Editor.

### 4. Start the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Architecture

The backend follows a layered architecture:

```
Client (chatUI)
    ↓ HTTP + X-User-Email header
main.py
    ↓
ChatController          (HTTP layer: routes, headers, query params)
    ↓
ChatService             (business logic, validation, authorization)
    ↓
Repositories            (Supabase table operations)
    ↓
Supabase client         (PostgREST)
    ↓
PostgreSQL (Supabase)
```

### Layer responsibilities

| Layer | Location | Responsibility |
|---|---|---|
| **Controller** | `controllers/chat_controller.py` | Defines API routes, extracts request data, delegates to service |
| **Service** | `services/chat_service.py` | Core business logic, validation, membership/creator checks, model → schema mapping |
| **Repository** | `repositories/` | CRUD operations against Supabase tables |
| **Model** | `models/` | Domain objects representing database rows |
| **Schema** | `schemas/` | API request/response contracts (one class per file) |

### Request flow example

```
POST /api/groups/{id}/members
  → ChatController.add_group_member()     # reads header + body
  → ChatService.add_group_member()        # validates creator, looks up user, saves membership
  → MembershipRepository.save()           # inserts into Supabase
```

`main.py` only bootstraps the app:

```python
chat_controller = ChatController()
app.include_router(chat_controller.router)
```

## Authentication

There is no JWT/session middleware. The frontend sends the signed-in user's email via the `X-User-Email` header (stored in a browser cookie). `ChatService` uses this to:
- Look up the user
- Verify group membership before chat or member operations
- Restrict "add member" to the group creator

## API endpoints

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Welcome message |
| `GET` | `/health` | Health check |

### Users

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/go` | Sign in / register user; returns name, email, and member groups |

**Request body:** `{ "name": "...", "email": "..." }`

### Groups

| Method | Path | Headers | Description |
|---|---|---|---|
| `GET` | `/api/groups` | `X-User-Email` | List groups the user belongs to |
| `POST` | `/api/groups` | `X-User-Email` | Create a group (creator is auto-added as member) |
| `POST` | `/api/groups/{group_id}/members` | `X-User-Email` | Add a member by email (creator only) |

**Create group body:** `{ "name": "..." }`

**Add member body:** `{ "email": "..." }`

Group response shape:
```json
{ "id": "uuid", "name": "Group name", "created_by": "creator@example.com" }
```

### Messages

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/messages` | Send a message to a group |
| `GET` | `/api/groups/{group_id}/messages/latest` | Poll for latest messages |
| `GET` | `/api/groups/{group_id}/messages/history` | Load older messages |

**Send message body:** `{ "body": "...", "group_id": "uuid" }`

**Latest messages query params:**
- No `after` → returns the latest 20 messages
- `after=<iso_timestamp>` → returns messages newer than that timestamp (for polling)

**History query params:**
- `before=<iso_timestamp>` → returns up to 20 messages older than that timestamp

## How it works

### Sign-in (`POST /api/go`)
1. `ChatService` upserts user by email in `users`
2. Fetches all groups linked via `memberships`
3. Returns user info and group list

### Create group
1. `ChatService` validates group name and user existence
2. `GroupRepository` inserts row into `groups` with `created_by`
3. Creator is added to `memberships`

### Add member
1. `ChatService` verifies caller is the group creator
2. Looks up target email in `users` — returns `404 User not found` if missing
3. `MembershipRepository` inserts into `memberships` (idempotent if already a member)

### Chat polling
1. Initial load: latest 20 messages, ascending by `created_at`
2. Poll every few seconds with `after=latest_timestamp` for new messages
3. "See older" uses `before=oldest_timestamp` to paginate history

## Error responses

| Status | When |
|---|---|
| `400` | Invalid input (empty name, invalid UUID, etc.) |
| `403` | Not a group member, or not the group creator |
| `404` | User or group not found |
| `500` | Supabase connection or unexpected server error |

## CORS

Configured for `http://localhost:5173` (Vite dev server). Update `allow_origins` in `main.py` for other environments.

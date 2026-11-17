import re
import secrets

from starlette.requests import Request
from starlette.responses import JSONResponse

from app import config, store
from app.service import bookings_view, conversation_summary, conversation_view, service

SESSION_ID_RE = re.compile(r"^[A-Za-z0-9+_-]{3,40}$")


def _error(message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


def _valid_id(session_id: str) -> bool:
    return SESSION_ID_RE.match(session_id) is not None


async def list_conversations(request: Request) -> JSONResponse:
    items = [conversation_summary(item["state"], item["updated_at"]) for item in store.list_states()]
    return JSONResponse({"conversations": items})


async def create_conversation(request: Request) -> JSONResponse:
    session_id = "web-" + secrets.token_hex(4)
    state = service.create_conversation(session_id)
    return JSONResponse(conversation_view(state), status_code=201)


async def get_conversation(request: Request) -> JSONResponse:
    session_id = request.path_params["session_id"]
    if not _valid_id(session_id):
        return _error("invalid conversation id", 400)
    state = store.load_state(session_id)
    if state is None:
        return _error("conversation not found", 404)
    return JSONResponse(conversation_view(state))


async def delete_conversation(request: Request) -> JSONResponse:
    session_id = request.path_params["session_id"]
    if not _valid_id(session_id):
        return _error("invalid conversation id", 400)
    if not store.delete_state(session_id):
        return _error("conversation not found", 404)
    return JSONResponse({"deleted": True})


async def post_message(request: Request) -> JSONResponse:
    session_id = request.path_params["session_id"]
    if not _valid_id(session_id):
        return _error("invalid conversation id", 400)
    try:
        body = await request.json()
    except ValueError:
        return _error("request body must be valid JSON", 400)
    text = str(body.get("text", "")).strip() if isinstance(body, dict) else ""
    if not text:
        return _error("message text is required", 400)
    if len(text) > config.MAX_MESSAGE_LENGTH:
        return _error("message is too long", 413)
    state = await service.handle_message(session_id, text)
    return JSONResponse(conversation_view(state))


async def list_bookings(request: Request) -> JSONResponse:
    return JSONResponse({"bookings": bookings_view()})

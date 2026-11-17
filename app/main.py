from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app import config, store
from app.api import chat, whatsapp


@asynccontextmanager
async def lifespan(app: Starlette):
    store.initialize()
    yield


async def index(request: Request) -> FileResponse:
    return FileResponse(config.STATIC_DIR / "index.html")


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


routes = [
    Route("/", index),
    Route("/health", health),
    Route("/api/conversations", chat.list_conversations, methods=["GET"]),
    Route("/api/conversations", chat.create_conversation, methods=["POST"]),
    Route("/api/conversations/{session_id}", chat.get_conversation, methods=["GET"]),
    Route("/api/conversations/{session_id}", chat.delete_conversation, methods=["DELETE"]),
    Route("/api/conversations/{session_id}/messages", chat.post_message, methods=["POST"]),
    Route("/api/bookings", chat.list_bookings, methods=["GET"]),
    Route("/whatsapp/webhook", whatsapp.verify_webhook, methods=["GET"]),
    Route("/whatsapp/webhook", whatsapp.handle_incoming_msg, methods=["POST"]),
    Mount("/static", app=StaticFiles(directory=str(config.STATIC_DIR)), name="static"),
]

app = Starlette(routes=routes, lifespan=lifespan)

import hashlib
import hmac
import json
import logging
from typing import Any, Optional

from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from app import config
from app.api import whatsapp_client
from app.dedupe import deduplicator
from app.service import service

logger = logging.getLogger("whatsapp")


def extract_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    items = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for message in value.get("messages") or []:
                if message.get("type") != "text":
                    continue
                body = str((message.get("text") or {}).get("body", "")).strip()
                message_id = message.get("id")
                sender = message.get("from")
                if body and message_id and sender:
                    items.append({"id": str(message_id), "phone": str(sender), "text": body})
    return items


def signature_valid(raw_body: bytes, header: Optional[str]) -> bool:
    if not config.WHATSAPP_APP_SECRET:
        return True
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(config.WHATSAPP_APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):])


async def process_messages(items: list[dict[str, str]]) -> None:
    for item in items:
        try:
            state = await service.handle_message(item["phone"], item["text"][: config.MAX_MESSAGE_LENGTH])
            await whatsapp_client.send_text(item["phone"], state["reply"])
        except Exception:
            logger.exception("failed to process WhatsApp message %s", item["id"])


async def verify_webhook(request: Request) -> PlainTextResponse:
    params = request.query_params
    token_ok = bool(config.WHATSAPP_VERIFY_TOKEN) and hmac.compare_digest(
        params.get("hub.verify_token", ""), config.WHATSAPP_VERIFY_TOKEN
    )
    if params.get("hub.mode") == "subscribe" and token_ok:
        return PlainTextResponse(params.get("hub.challenge", ""))
    return PlainTextResponse("forbidden", status_code=403)


async def handle_incoming_msg(request: Request) -> JSONResponse:
    raw_body = await request.body()
    if not signature_valid(raw_body, request.headers.get("x-hub-signature-256")):
        return JSONResponse({"error": "invalid signature"}, status_code=403)
    try:
        payload = json.loads(raw_body or b"{}")
    except ValueError:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "invalid payload"}, status_code=400)
    fresh = [item for item in extract_messages(payload) if deduplicator.claim(item["id"])]
    task = BackgroundTask(process_messages, fresh) if fresh else None
    return JSONResponse({"status": "received", "accepted": len(fresh)}, background=task)

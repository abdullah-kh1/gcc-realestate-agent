import asyncio
import json
import logging
import urllib.error
import urllib.request

from app import config

logger = logging.getLogger("whatsapp")

GRAPH_API_VERSION = "v21.0"
REQUEST_TIMEOUT_SECONDS = 10


def _post(to: str, body: str) -> bool:
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = json.dumps(
        {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}}
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError):
        logger.exception("WhatsApp send failed")
        return False


async def send_text(to: str, body: str) -> bool:
    if not (config.WHATSAPP_ACCESS_TOKEN and config.WHATSAPP_PHONE_NUMBER_ID):
        logger.info("WhatsApp credentials not configured, reply was stored only")
        return False
    return await asyncio.to_thread(_post, to, body)

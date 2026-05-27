"""
Zana Webhook Server
────────────────────
FastAPI server that:
  1. Verifies the WhatsApp webhook on startup (GET /webhook)
  2. Receives inbound messages (POST /webhook)
  3. Routes each message through the Zana orchestrator
  4. Starts the scheduler for proactive jobs
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse

from config.settings import WHATSAPP_VERIFY_TOKEN
from agents.orchestrator import handle_message
from models.schemas import IncomingMessage
from schedulers.trigger_engine import create_scheduler
from tools.whatsapp_tool import parse_webhook
from database.firestore_client import get_clinic_by_whatsapp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("zana.server")


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 Zana starting up...")
    scheduler = create_scheduler()
    scheduler.start()
    log.info("⏰ Scheduler started")
    yield
    scheduler.shutdown()
    log.info("👋 Zana shutting down")

app = FastAPI(title="Zana", version="1.0.0", lifespan=lifespan)


# ── Webhook verification ───────────────────────────────────────────────────────
# Meta calls this once when you register the webhook URL in the dashboard.

@app.get("/webhook")
async def verify_webhook(
    hub_mode:        str = Query(alias="hub.mode"),
    hub_challenge:   str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        log.info("✅ WhatsApp webhook verified")
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


# ── Inbound message handler ───────────────────────────────────────────────────

@app.post("/webhook")
async def receive_message(request: Request):
    """
    WhatsApp sends every message event here.
    We parse → route → respond. Always return 200 immediately
    (Meta will retry if we don't, causing duplicate messages).
    """
    payload = await request.json()
    parsed  = parse_webhook(payload)

    if not parsed:
        # Not a text message (delivery receipt, read receipt, etc.) — ignore
        return {"status": "ignored"}

    log.info(f"📨 Message from {parsed['from_phone']}: {parsed['message_body'][:60]}")

    # Identify which clinic this WhatsApp number belongs to
    clinic = get_clinic_by_whatsapp(parsed["to_phone"])
    if not clinic:
        log.warning(f"⚠️ No clinic found for WhatsApp number {parsed['to_phone']}")
        return {"status": "unknown_clinic"}

    # Build a structured message object
    msg = IncomingMessage(
        from_phone  = parsed["from_phone"],
        message_body = parsed["message_body"],
        message_id  = parsed["message_id"],
        timestamp   = datetime.utcnow(),
        clinic_id   = clinic.clinic_id,
    )

    # Update patient name if WhatsApp provides it
    from database.firestore_client import update_patient, get_or_create_patient
    patient = get_or_create_patient(msg.from_phone, clinic.clinic_id)
    if not patient.name and parsed.get("name"):
        update_patient(msg.from_phone, {"name": parsed["name"]})

    # Hand off to orchestrator (non-blocking — always return 200 to Meta)
    try:
        await handle_message(msg)
    except Exception as e:
        log.error(f"❌ Orchestrator error: {e}", exc_info=True)

    return {"status": "ok"}


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Zana"}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webhook.server:app", host="0.0.0.0", port=8000, reload=True)

import logging
import traceback

from fastapi import Body, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from campaign_service import (
    generate_bulk_email_bodies as build_email_bodies,
    generate_bulk_subject_lines as build_subject_lines,
    generate_full_campaign as build_campaign,
    load_customers,
)
from config import CREDENTIALS_FILE, CUSTOMERS_CSV, FRONTEND_DIR, GEMINI_API_KEY, TOKEN_FILE
from gemini_service import generate_text, list_model_names
from gmail_service import gmail_status, reconnect_gmail, send_email as deliver_email
from logging_config import configure_logging
from schemas import EmailRequest

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Email Campaign API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def frontend():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Backend running with Gemini + Gmail!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    gmail = gmail_status()
    checks = {
        "gemini_api_key": bool(GEMINI_API_KEY),
        "gmail_credentials": CREDENTIALS_FILE.exists(),
        "gmail_token": bool(gmail.get("token_valid")),
        "customers_csv": CUSTOMERS_CSV.exists(),
        "frontend": (FRONTEND_DIR / "index.html").exists(),
    }
    return {"ready": all(checks.values()), "checks": checks, "gmail": gmail}


@app.get("/gmail/status")
def get_gmail_status():
    return gmail_status()


@app.post("/gmail/reconnect")
def reconnect():
    try:
        return reconnect_gmail()
    except Exception as exc:
        logger.error("Error reconnecting Gmail: %s", traceback.format_exc())
        return {"error": str(exc)}


@app.post("/send")
def send_email(
    payload: EmailRequest | None = Body(default=None),
    to: str | None = Query(default=None),
    subject: str | None = Query(default=None),
    body: str | None = Query(default=None),
):
    try:
        request = payload or EmailRequest(to=to, subject=subject, body=body)
        return deliver_email(request.to, request.subject, request.body)
    except Exception as exc:
        logger.error("Error sending email: %s", traceback.format_exc())
        return {"error": str(exc)}


@app.get("/test")
def test_gemini():
    try:
        output = generate_text("Write exactly one short greeting sentence. Output plain text only.")
        return {"output": output}
    except Exception as exc:
        logger.error("Error in /test: %s", traceback.format_exc())
        return {"error": str(exc)}


@app.get("/models")
def list_models():
    try:
        return {"models": list_model_names()}
    except Exception as exc:
        logger.error("Error listing models: %s", traceback.format_exc())
        return {"error": str(exc)}


@app.get("/customers")
def list_customers():
    try:
        return {"customers": load_customers()}
    except Exception as exc:
        logger.error("Error in /customers: %s", traceback.format_exc())
        return {"error": str(exc)}


@app.get("/subjectlines")
def generate_bulk_subject_lines():
    try:
        return {"results": build_subject_lines()}
    except Exception as exc:
        logger.error("Error in /subjectlines: %s", traceback.format_exc())
        return {"error": str(exc)}


@app.get("/emailbodies")
def generate_bulk_email_bodies():
    try:
        return {"results": build_email_bodies()}
    except Exception as exc:
        logger.error("Error in /emailbodies: %s", traceback.format_exc())
        return {"error": str(exc)}


@app.get("/campaign")
def generate_full_campaign():
    try:
        return {"results": build_campaign()}
    except Exception as exc:
        logger.error("Error in /campaign: %s", traceback.format_exc())
        return {"error": str(exc)}

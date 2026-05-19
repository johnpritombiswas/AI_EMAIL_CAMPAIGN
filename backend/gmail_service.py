import base64
import logging
from email.mime.text import MIMEText

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, TOKEN_FILE

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def load_credentials():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    return creds


def run_oauth_flow():
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def get_gmail_service(force_reauth: bool = False):
    creds = None if force_reauth else load_credentials()

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            except RefreshError:
                logger.warning("Stored Gmail token is expired or revoked; starting OAuth again")
                if TOKEN_FILE.exists():
                    TOKEN_FILE.unlink()
                creds = run_oauth_flow()
        else:
            creds = run_oauth_flow()

    return build("gmail", "v1", credentials=creds)


def gmail_status() -> dict[str, object]:
    if not CREDENTIALS_FILE.exists():
        return {"configured": False, "token_file": TOKEN_FILE.exists(), "token_valid": False}

    creds = load_credentials()
    if not creds:
        return {"configured": True, "token_file": False, "token_valid": False}

    if creds.valid:
        return {"configured": True, "token_file": True, "token_valid": True}

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            return {"configured": True, "token_file": True, "token_valid": True}
        except RefreshError as exc:
            return {
                "configured": True,
                "token_file": True,
                "token_valid": False,
                "error": "Stored Gmail token expired or was revoked. Reconnect Gmail.",
                "details": str(exc),
            }

    return {
        "configured": True,
        "token_file": True,
        "token_valid": False,
        "error": "Stored Gmail token is incomplete. Reconnect Gmail.",
    }


def create_message(to: str, subject: str, body: str) -> dict[str, str]:
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_email(to: str, subject: str, body: str) -> dict[str, str]:
    service = get_gmail_service()
    message = create_message(to, subject, body)
    sent = service.users().messages().send(userId="me", body=message).execute()
    logger.info("Sent email to %s with message id %s", to, sent.get("id"))
    return {"status": "sent", "id": sent["id"]}


def reconnect_gmail() -> dict[str, object]:
    get_gmail_service(force_reauth=True)
    return gmail_status()

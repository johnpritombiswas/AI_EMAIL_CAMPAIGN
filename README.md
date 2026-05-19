# AI Email Campaign

FastAPI app for generating marketing email campaigns with Gemini, previewing/editing them in a browser UI, and sending selected emails through Gmail.

## Features

- Generate subject lines from `data/customers.csv`
- Generate short email bodies per recipient
- Preview and edit campaign emails before sending
- Send one-off emails from the UI
- Reconnect Gmail OAuth when the token expires
- Health/readiness endpoints for quick debugging

## Project Structure

```text
backend/
  main.py
  campaign_service.py
  gemini_service.py
  gmail_service.py
  config.py
  schemas.py
frontend/
  index.html
  styles.css
  app.js
data/
  customers.csv
run.ps1
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r backend\requirements.txt
```

Create `backend/.env` from the example file:

```powershell
Copy-Item backend\.env.example backend\.env
```

Then add your Gemini API key:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=models/gemini-2.5-pro
GEMINI_FALLBACK_MODEL=models/gemini-flash-lite-latest
```

## Gmail Setup

Place your Google OAuth client file here:

```text
backend/credentials.json
```

The app will create `backend/token.json` after you connect Gmail.

Both files are ignored by Git because they contain secrets or account-specific credentials.

## Run

From the project root:

```powershell
.\run.ps1
```

Then open:

```text
http://127.0.0.1:8000/
```

Manual start:

```powershell
cd backend
.\venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000 --reload
```

## Workflow

1. Click **Check readiness**.
2. If Gmail is disconnected, click **Reconnect Gmail** and complete Google sign-in.
3. Click **Load recipients** to load `data/customers.csv`.
4. Generate **Subject lines**, **Email bodies**, or the full **Generate preview**.
5. Edit the generated email cards.
6. Send selected emails.

## Recipients CSV

`data/customers.csv` must include:

```csv
name,email
Sarah,sarah@example.com
```

## Useful Endpoints

```text
GET  /
GET  /health
GET  /ready
GET  /customers
GET  /gmail/status
POST /gmail/reconnect
GET  /subjectlines
GET  /emailbodies
GET  /campaign
POST /send
```

`POST /send` accepts JSON:

```json
{
  "to": "recipient@example.com",
  "subject": "Subject line",
  "body": "Email body"
}
```

## GitHub Notes

Do commit:

```text
backend/*.py
frontend/*
data/customers.csv
backend/.env.example
backend/requirements.txt
requirements.txt
README.md
run.ps1
.gitignore
```

Do not commit:

```text
backend/.env
backend/credentials.json
backend/token.json
backend/venv/
backend/logs/
```

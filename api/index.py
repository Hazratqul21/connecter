"""
Connecter Middleware: Binotel -> HelpDeskEddy
Single File Deployment for Vercel
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import datetime
import pytz
from typing import Dict, Any
from functools import lru_cache

# --- Configuration (Merged) ---
class Settings:
    """Production configuration with hardcoded credentials"""
    APP_NAME: str = "Connecter Middleware (Binotel -> HDE)"
    APP_VERSION: str = "3.1.0"
    
    # Binotel WebSocket/API Credentials
    BINOTEL_WEB_KEY: str = "114e5e-5e61a64"
    BINOTEL_WEB_SECRET: str = "4e8039-d5385d-bfd84c-f07be4-771ce163"
    
    # HelpDeskEddy Integration
    HELPDESKEDDY_URL: str = "https://qwatt.helpdeskeddy.com/api/v2/telephony/calls/DyJmRuiZTsqsXyRsegJR"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

# --- App Initialization ---
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# --- Global State ---
last_transaction: Dict[str, Any] = {
    "status": "No calls processed yet",
    "timestamp": str(datetime.datetime.now())
}

# --- Utilities ---
def get_tashkent_time() -> str:
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def transform_binotel_to_hde(binotel_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transforms Binotel 'apiCallCompleted' data to HelpDeskEddy format."""
    call_id = binotel_data.get('callDetails[generalCallID]', '0')
    phone = binotel_data.get('callDetails[externalNumber]', '')
    extension = binotel_data.get('callDetails[internalNumber]', '')
    disposition = binotel_data.get('callDetails[disposition]', 'UNKNOWN')
    duration = binotel_data.get('callDetails[billsec]', '0')
    recording_url = binotel_data.get('callDetails[linkToCallRecordInMyBusiness]', '')
    
    status = "completed"
    if disposition == "ANSWER":
        status = "completed"
    elif disposition in ["NO ANSWER", "BUSY", "CANCEL"]:
        status = "missed"
    
    return {
        "action": "create_call",
        "uuid": call_id,
        "direction": "incoming",
        "phone": phone,
        "extension": extension,
        "status": status,
        "duration": duration,
        "recording_url": recording_url,
        "timestamp": get_tashkent_time()
    }

# --- Endpoints ---
@app.get("/")
async def root():
    """Displays the LAST processed transaction."""
    return JSONResponse(content=last_transaction, status_code=200)

@app.all("/webhook")
async def webhook_handler(request: Request):
    global last_transaction
    
    if request.method == "GET":
        return {"status": "Webhook is active. Send POST request."}

    # 1. Parse
    form_data = await request.form()
    payload = dict(form_data)
    
    if payload.get("requestType") != "apiCallCompleted":
        return {"status": "ignored", "reason": f"Event type {payload.get('requestType')} not handled"}

    # 2. Transform
    hde_payload = transform_binotel_to_hde(payload)
    
    # 3. Send
    hde_response_code = 0
    hde_response_body = ""
    try:
        response = requests.post(
            settings.HELPDESKEDDY_URL,
            data=hde_payload,
            timeout=10
        )
        hde_response_code = response.status_code
        hde_response_body = response.text
    except Exception as e:
        hde_response_code = 500
        hde_response_body = str(e)

    # 4. Log
    last_transaction = {
        "received_at": get_tashkent_time(),
        "payload": payload,
        "transformed_for_hde": hde_payload,
        "hde_response_code": hde_response_code,
        "hde_response_body": hde_response_body
    }
    
    return {"status": "success", "generalCallID": hde_payload["uuid"]}
# Set root_path to /api for Vercel deployment
# This ensures that requests to /api/endpoint are correctly routed to /endpoint in FastAPI
app.root_path = "/api"

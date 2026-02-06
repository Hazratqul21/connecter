"""
Connecter Middleware: Binotel -> HelpDeskEddy
Simple, linear, hardcoded.
"""
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse
import requests
import datetime
import json
import pytz
from typing import Optional, Dict, Any

from backend.src.core.config import settings

app = FastAPI(title="Connecter Middleware", version="3.0.0")

# --- Global State (In-Memory) ---
# Stores the DETAILS of the last processed transaction for display at /
last_transaction: Dict[str, Any] = {
    "status": "No calls processed yet",
    "timestamp": str(datetime.datetime.now())
}

# --- Utilities ---
def get_tashkent_time() -> str:
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def transform_binotel_to_hde(binotel_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms Binotel 'apiCallCompleted' data to HelpDeskEddy format.
    """
    # Extract nested fields (Binotel sends flat form keys like 'callDetails[generalCallID]')
    # We rely on the fact that python-multipart parsing might or might not handle nested brackets nicely.
    # If we receive raw form data, we access it by keys.
    
    # Defaults
    call_id = binotel_data.get('callDetails[generalCallID]', '0')
    phone = binotel_data.get('callDetails[externalNumber]', '')
    extension = binotel_data.get('callDetails[internalNumber]', '')
    disposition = binotel_data.get('callDetails[disposition]', 'UNKNOWN')
    duration = binotel_data.get('callDetails[billsec]', '0')
    recording_url = binotel_data.get('callDetails[linkToCallRecordInMyBusiness]', '')
    
    # Status Mapping
    status = "completed"
    if disposition == "ANSWER":
        status = "completed"
    elif disposition in ["NO ANSWER", "BUSY", "CANCEL"]:
        status = "missed"
    
    return {
        "action": "create_call",
        "uuid": call_id,
        "direction": "incoming", # Binotel 'callDetails[callType]'=0 is incoming, 1 is outgoing. Assuming incoming for now or logic:
        # callType: 0 - incoming, 1 - outgoing
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
    """
    Displays the LAST processed transaction in the requested format.
    """
    return JSONResponse(content=last_transaction, status_code=200)

@app.all("/webhook") # Support both POST and GET (Binotel sometimes checks GET)
async def webhook_handler(request: Request):
    """
    Main Handler:
    1. Parse Binotel Form Data
    2. Transform
    3. Send to HDE
    4. Update Global State
    """
    global last_transaction
    
    if request.method == "GET":
        return {"status": "Webhook is active. Send POST request."}

    # 1. Parse Data
    # Binotel sends data as application/x-www-form-urlencoded
    form_data = await request.form()
    # Convert FormData to plain dict for JSON serialization/logging
    payload = dict(form_data)
    
    # Check if this is the right event type
    request_type = payload.get("requestType")
    
    # We explicitly only care about 'apiCallCompleted' as per user instruction
    if request_type != "apiCallCompleted":
        return {"status": "ignored", "reason": f"Event type {request_type} not handled"}

    # 2. Transform
    hde_payload = transform_binotel_to_hde(payload)
    
    # 3. Send to HelpDeskEddy
    hde_response_code = 0
    hde_response_body = ""
    
    try:
        response = requests.post(
            settings.HELPDESKEDDY_URL,
            data=hde_payload, # requests sends form-encoded by default if data is dict, HDE usually expects form data
            timeout=10
        )
        hde_response_code = response.status_code
        hde_response_body = response.text
    except Exception as e:
        hde_response_code = 500
        hde_response_body = str(e)

    # 4. Update Global Transaction Log
    last_transaction = {
        "received_at": get_tashkent_time(),
        "payload": payload,
        "transformed_for_hde": hde_payload,
        "hde_response_code": hde_response_code,
        "hde_response_body": hde_response_body
    }
    
    # 5. Return Success to Binotel
    return {"status": "success", "generalCallID": hde_payload["uuid"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

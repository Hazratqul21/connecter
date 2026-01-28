from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse
import logging
import json
import requests
from datetime import datetime
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Credentials & Config
BINOTEL_API_KEY = "70206a-84faf4d"
BINOTEL_API_SECRET = "e4a051-9d3c02-7cdb1a-a5d224-f8406eda"
HELPDESKEDDY_URL = "https://qwatt.helpdeskeddy.com/api/v2/telephony/calls/DyJmRuiZTsqsXyRsegJR"

@app.get("/webhook", response_class=HTMLResponse)
async def webhook_status():
    """
    Status page for the middleware.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""
    <html>
        <head>
            <title>Middleware Status</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }}
                .status {{ font-size: 24px; color: green; font-weight: bold; }}
                .time {{ font-size: 18px; color: #555; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="status">System is Operational</div>
            <div class="time">Server Time: {current_time}</div>
        </body>
    </html>
    """
    return html_content

@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Main webhook handler for Binotel events.
    Accepts both JSON and Form Data.
    """
    try:
        # 1. Parse incoming data (Form or JSON)
        content_type = request.headers.get("Content-Type", "")
        payload = {}
        
        if "application/json" in content_type:
            payload = await request.json()
        else:
            form_data = await request.form()
            payload = dict(form_data)

        # 2. Log incoming data using json.dumps for pretty printing in logs
        logger.info(f"Incoming Webhook Payload:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")

        # 3. Filter: Only process 'apiCallCompleted'
        request_type = payload.get("requestType")
        if request_type != "apiCallCompleted":
            logger.info(f"Ignored requestType: {request_type}")
            return {"status": "ignored", "reason": "Not apiCallCompleted"}

        # 4. Transform data for HelpDeskEddy
        # Mapping logic based on Binotel common fields and user requirements
        
        # Determine call type (inbound/outbound)
        # Check 'direction' (incoming/outgoing) OR 'callType' (0=inbound, 1=outbound)
        direction_raw = payload.get("direction", "")
        call_type_raw = str(payload.get("callType", ""))
        
        if direction_raw == "outgoing" or call_type_raw == "1":
            call_type = "outbound"
        else:
            call_type = "inbound"

        # Correct mapping of status
        # Binotel 'disposition' often holds values like 'ANSWER', 'NO ANSWER', 'BUSY'
        # User wants "completed" or "missed".
        disposition = payload.get("disposition", "").upper()
        # 'billsec' > 0 usually implies completed for billing purposes, but 'ANSWER' is safer.
        status = "completed" if disposition == "ANSWER" or (payload.get("billsec", 0) and int(payload.get("billsec", 0)) > 0) else "missed"

        # Transform
        hde_payload = {
            "uuid": payload.get("generalCallID"),
            "type": call_type,
            "phone": payload.get("externalNumber"),
            "extension": payload.get("internalNumber"),
            "status": status,
            "duration": payload.get("billsec"),
            "recording_url": payload.get("linkToCallRecordInMyBusiness") or payload.get("recordingUrl") or "",
            "timestamp": payload.get("startTime")
        }

        logger.info(f"Transformed Payload for HelpDeskEddy:\n{json.dumps(hde_payload, indent=2)}")

        # 5. Send to HelpDeskEddy
        # Using requests to send POST
        response = requests.post(HELPDESKEDDY_URL, json=hde_payload)
        
        # 6. Log response
        logger.info(f"HelpDeskEddy Response Status: {response.status_code}")
        logger.info(f"HelpDeskEddy Response Body: {response.text}")

        return {"status": "processed", "forwarded_to_hde": True, "hde_status": response.status_code}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "error": str(e)})

# Vercel entry point
# This is often needed for Vercel if it looks for an 'app' variable in the module
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

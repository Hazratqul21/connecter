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

# In-memory storage for the last received payload (for debugging)
last_webhook_payload = {"status": "No data received yet"}

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Root endpoint to show system status and last received webhook.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload_str = json.dumps(last_webhook_payload, indent=2, ensure_ascii=False)
    
    html_content = f"""
    <html>
        <head>
            <title>Connecter Middleware</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .status {{ font-size: 24px; color: green; font-weight: bold; margin-bottom: 20px; }}
                .info {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                pre {{ background: #333; color: #fff; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                .refresh {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="status">System is Operational</div>
            <div class="info">
                <p><strong>Server Time:</strong> {current_time}</p>
                <p><strong>Endpoint:</strong> POST /webhook</p>
            </div>
            
            <h3>Last Received Webhook Payload:</h3>
            <pre>{payload_str}</pre>
            
            <div class="refresh">
                <button onclick="location.reload()">Refresh Data</button>
            </div>
        </body>
    </html>
    """
    return html_content

@app.get("/webhook", response_class=HTMLResponse)
async def webhook_status():
    """
    Redirects to root or shows status.
    """
    return await root()

@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Main webhook handler for Binotel events.
    Accepts both JSON and Form Data.
    """
    global last_webhook_payload
    try:
        # 1. Parse incoming data (Form or JSON)
        content_type = request.headers.get("Content-Type", "")
        payload = {}
        
        if "application/json" in content_type:
            try:
                payload = await request.json()
            except Exception:
                payload = {"error": "Invalid JSON body"}
        else:
            form_data = await request.form()
            payload = dict(form_data)

        # Update last payload for debugging
        last_webhook_payload = {
            "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payload": payload
        }

        # 2. Log incoming data using json.dumps for pretty printing in logs
        logger.info(f"Incoming Webhook Payload:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")

        # 3. Filter: Only process 'apiCallCompleted' (unless it's a test)
        request_type = payload.get("requestType")
        is_test = payload.get("isTest") == "true"
        
        if request_type != "apiCallCompleted" and not is_test:
            logger.info(f"Ignored requestType: {request_type}")
            return {"status": "ignored", "reason": "Not apiCallCompleted"}

        # 4. Transform data for HelpDeskEddy
        def get_binotel_field(data, key):
            """
            Helper to find values either in flat format (key) 
            or nested format (callDetails[key]).
            """
            if key in data:
                return data[key]
            nested_key = f"callDetails[{key}]"
            if nested_key in data:
                return data[nested_key]
            return None

        # Extract fields using the helper
        general_call_id = get_binotel_field(payload, "generalCallID") or "unknown_id"
        if not general_call_id or general_call_id == "unknown_id":
             general_call_id = get_binotel_field(payload, "callID")

        external_number = get_binotel_field(payload, "externalNumber")
        internal_number = get_binotel_field(payload, "internalNumber")
        billsec = get_binotel_field(payload, "billsec")
        start_time_raw = get_binotel_field(payload, "startTime")
        disposition = get_binotel_field(payload, "disposition")
        
        # Link to record
        link_to_record = get_binotel_field(payload, "linkToCallRecordInMyBusiness")
        if not link_to_record:
            link_to_record = get_binotel_field(payload, "recordingUrl")

        # Determine call type (inbound/outbound)
        direction_raw = payload.get("direction", "") 
        call_type_value = get_binotel_field(payload, "callType")
        
        call_type = "inbound" # Default
        if direction_raw == "outgoing" or str(call_type_value) == "1":
            call_type = "outbound"

        # Correct mapping of status
        disposition_upper = str(disposition).upper() if disposition else ""
        
        status = "missed" # Default
        if disposition_upper == "ANSWER":
             status = "completed"
        elif billsec and str(billsec).isdigit() and int(billsec) > 0:
             status = "completed"
        if "ОТВЕТ" in disposition_upper:
            status = "completed"
            
        # Timestamp Formatting Fix: Convert Unix to YYYY-MM-DD HH:MM:SS
        formatted_start_time = ""
        if start_time_raw:
            try:
                # Check if it's already formatted
                if "-" in str(start_time_raw) and ":" in str(start_time_raw):
                    formatted_start_time = str(start_time_raw)
                else:
                    # Assume unix timestamp
                    ts = int(start_time_raw)
                    formatted_start_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logger.warning(f"Failed to convert timestamp {start_time_raw}: {e}")
                formatted_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            formatted_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Transform
        hde_payload = {
            "action": "create_call", # REQUIRED by HDE
            "uuid": general_call_id,
            "direction": call_type, # REQUIRED (renamed from 'type')
            "phone": external_number,
            "extension": internal_number,
            "status": status,
            "duration": billsec,
            "recording_url": link_to_record or "",
            "timestamp": formatted_start_time
        }
        
        # Add transformation debugging info
        last_webhook_payload["transformed_for_hde"] = hde_payload

        logger.info(f"Transformed Payload for HelpDeskEddy:\n{json.dumps(hde_payload, indent=2)}")

        # 5. Send to HelpDeskEddy
        # IMPORTANT: Send as Form Data (data=...), NOT JSON
        response = requests.post(HELPDESKEDDY_URL, data=hde_payload)
        
        # 6. Log response
        logger.info(f"HelpDeskEddy Response Status: {response.status_code}")
        logger.info(f"HelpDeskEddy Response Body: {response.text}")
        
        # Add HDE response to debugging
        last_webhook_payload["hde_response_code"] = response.status_code
        last_webhook_payload["hde_response_body"] = response.text

        return {"status": "processed", "forwarded_to_hde": True, "hde_status": response.status_code, "hde_res": response.text}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "error": str(e)})

@app.get("/simulate", response_class=HTMLResponse)
async def simulate_call():
    """
    DEBUG TOOL: Simulates a call request to HelpDeskEddy.
    Use this to verify if the connection to HelpDeskEddy works,
    independent of Binotel.
    """
    try:
        # Create a dummy payload mimicking what we extracted
        dummy_hde_payload = {
            "action": "create_call",
            "uuid": f"test-{int(datetime.now().timestamp())}",
            "direction": "incoming",
            "phone": "998901234567", # Test phone
            "extension": "903", # Using 903 (Hasan)
            "status": "completed",
            "duration": "120",
            "recording_url": "https://example.com/test_record.mp3",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info("Running simulation...")
        # IMPORTANT: Send as Form Data
        response = requests.post(HELPDESKEDDY_URL, data=dummy_hde_payload)
        
        return f"""
        <html>
            <body style="font-family: monospace; padding: 20px;">
                <h1>Simulation Result</h1>
                <p><strong>Sent Payload:</strong></p>
                <pre>{json.dumps(dummy_hde_payload, indent=2)}</pre>
                <hr>
                <p><strong>HelpDeskEddy Response ({response.status_code}):</strong></p>
                <pre>{response.text}</pre>
                <hr>
                <p>If the response code is 200, check HelpDeskEddy tickets for a call from 998901234567.</p>
                <button onclick="window.history.back()">Go Back</button>
            </body>
        </html>
        """
    except Exception as e:
        return f"<h1>Error in simulation</h1><p>{str(e)}</p>"

# Vercel entry point
# This is often needed for Vercel if it looks for an 'app' variable in the module
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

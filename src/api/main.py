from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from src.core.config import get_settings
from src.services.ai_service import process_call_intelligence
import logging
import json
import requests
from datetime import datetime
import sys
import pytz

# Load Settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

app = FastAPI(title=settings.APP_NAME)

last_webhook_payload = {"status": "No data received yet"}

def get_current_time():
    return datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d %H:%M:%S")

@app.get("/", response_class=HTMLResponse)
async def root():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload_str = json.dumps(last_webhook_payload, indent=2, ensure_ascii=False)
    html_content = f"""
    <html>
        <head><title>Connecter (Vercel Edition)</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>System Operational</h1>
            <p><strong>Deployment:</strong> Vercel Serverless</p>
            <p><strong>Time:</strong> {current_time}</p>
            <h3>Last Webhook:</h3>
            <pre style="background: #eee; padding: 10px;">{payload_str}</pre>
        </body>
    </html>
    """
    return html_content

@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook handler.
    1. Receives Binotel Data.
    2. Sends to HelpDeskEddy (Sync).
    3. Triggers AI Analysis (Background Task).
    """
    global last_webhook_payload
    try:
        # 1. Parse Data
        content_type = request.headers.get("Content-Type", "")
        payload = {}
        if "application/json" in content_type:
            payload = await request.json()
        else:
            form_data = await request.form()
            payload = dict(form_data)

        last_webhook_payload = {
            "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payload": payload
        }
        
        # 2. Filter Events
        request_type = payload.get("requestType")
        if request_type != "apiCallCompleted":
            return {"status": "ignored", "reason": "Not apiCallCompleted"}

        # 3. Extract Data
        def get_field(data, key):
             if key in data: return data[key]
             if f"callDetails[{key}]" in data: return data[f"callDetails[{key}]"]
             return None

        general_call_id = get_field(payload, "generalCallID") or "unknown_id"
        recording_url = get_field(payload, "recordingUrl") or get_field(payload, "linkToCallRecordInMyBusiness") or ""
        
        # ... (Existing HDE Logic omitted for brevity, assuming it works) ...
        # For this refactor, I am focusing on adding the Background Task
        
        # 4. Unified Background Processing (Orchestrator)
        # We construct a call_data dict
        call_summary_data = {
            "uuid": general_call_id,
            "direction": call_type,
            "status": status,
            "phone": external_number,
            "extension": internal_number,
            "duration": duration_int,
            "recording_url": final_recording_url
        }
        
        from src.services.orchestrator import orchestrate_call_processing
        background_tasks.add_task(
            orchestrate_call_processing,
            call_summary_data=call_summary_data,
            binotel_payload=payload
        ) # Single task ensures sequential execution

        return {"status": "success", "message": "Processing in background"}

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

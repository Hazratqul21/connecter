from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import requests
import json
import logging
import sys
import time
import traceback
from datetime import datetime

# --- 1. SENIOR DARAJADAGI LOGGING SOZLAMALARI ---
# Vercel konsolida rangli va tartibli ko'rinishi uchun
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("middleware")

app = FastAPI()

# --- 2. SOZLAMALAR (SIZNING MA'LUMOTLARINGIZ BILAN TAYYORLANDI) ---
# HelpDeskEddy Webhook manzili
HELPDESK_URL = "https://qwatt.helpdeskeddy.com/api/v2/telephony/calls/DyJmRuiZTsqsXyRsegJR"

# Binotel API Kalitlari (Siz yuborgan ma'lumotlar)
BINOTEL_API_KEY = "70206a-84faf4d"
BINOTEL_API_SECRET = "e4a051-9d3c02-7cdb1a-a5d224-f8406eda"

# --- 3. YORDAMCHI FUNKSIYA: JADVAL CHIZISH ---
def log_as_table(title: str, data: dict):
    """Vercel loglarida ma'lumotni jadval ko'rinishida chiqaradi"""
    table_border = "=" * 60
    logger.info(f"\n{table_border}")
    logger.info(f"📊 {title.upper()}")
    logger.info(f"{'-' * 60}")
    logger.info(f"{'KEY (KALIT)':<25} | {'VALUE (QIYMAT)'}")
    logger.info(f"{'-' * 60}")
    
    for key, value in data.items():
        val_str = str(value)
        # Juda uzun matnlarni qirqib ko'rsatamiz
        if len(val_str) > 100:
            val_str = val_str[:97] + "..."
        logger.info(f"{key:<25} | {val_str}")
    
    logger.info(f"{table_border}\n")

# --- 4. ASOSIY INTELLIGENT ROUTE ---
# GET (Brauzer) va POST (Binotel) ni bitta joyda ushlaymiz
@app.api_route("/webhook", methods=["GET", "POST"])
async def binotel_handler(request: Request):
    start_time = time.time() # Vaqtni o'lchashni boshlaymiz

    # --- A) AGAR BRAUZERDA OCHILSA (GET) ---
    if request.method == "GET":
        logger.info("Health Check: Tizim ishlamoqda (GET request)")
        html_content = f"""
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #2ecc71;">✅ Tizim 100% Ishlamoqda</h1>
                <p>Binotel va HelpDeskEddy o'rtasidagi ko'prik faol.</p>
                <div style="background: #f1f1f1; padding: 20px; border-radius: 10px; display: inline-block; text-align: left;">
                    <strong>Status:</strong> Online<br>
                    <strong>API Key:</strong> {BINOTEL_API_KEY[:4]}****<br>
                    <strong>Server Time:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
                    <strong>Mode:</strong> Production
                </div>
                <p style="color: #7f8c8d; margin-top: 20px;">Iltimos, ushbu linkni Binotel sozlamalariga kiriting (POST).</p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)

    # --- B) AGAR BINOTEL YUBORSA (POST) ---
    try:
        # 1. Ma'lumotni o'qib olish (Parsing)
        content_type = request.headers.get("content-type", "")
        data = {}

        if "application/json" in content_type:
            data = await request.json()
        else:
            form_data = await request.form()
            data = dict(form_data)
            # Binotel ba'zida JSONni string qilib yuboradi, shuni to'g'rilaymiz
            if 'requestType' not in data and len(data) == 1:
                key = list(data.keys())[0]
                try:
                    data = json.loads(key)
                except:
                    pass
            # Yana bir tekshiruv: agar body bo'sh bo'lmasa lekin data bo'sh bo'lsa
            if not data:
                raw_body = await request.body()
                try:
                    data = json.loads(raw_body)
                except:
                    pass

        # LOG: Kiruvchi ma'lumotni jadval qilib chiqarish
        log_as_table("1. BINOTELDAN KELGAN MA'LUMOT", data)

        # 2. Filtrlash (Faqat tugallangan qo'ng'iroqlar)
        request_type = data.get("requestType", "unknown")
        if request_type != "apiCallCompleted":
             logger.warning(f"⚠️  E'tiborsiz qoldirildi: requestType='{request_type}'")
             return {"status": "ignored", "reason": "Not a completed call event"}

        # 3. Ma'lumotlarni HelpDeskEddy formatiga o'tkazish (Transformation)
        external_number = data.get("externalNumber")
        internal_number = data.get("internalNumber")
        billsec = int(data.get("billsec", 0))
        call_type_raw = str(data.get("callType", "0")) # 0-kiruvchi, 1-chiquvchi
        recording_url = data.get("linkToCallRecordInMyBusiness")
        call_id = data.get("generalCallID")
        start_time_val = data.get("startTime")

        direction = "outbound" if call_type_raw == "1" else "inbound"
        call_status = "completed" if billsec > 0 else "missed"

        payload = {
            "uuid": call_id,
            "type": direction,
            "phone": external_number,
            "extension": internal_number,
            "status": call_status,
            "duration": billsec,
            "recording_url": recording_url,
            "timestamp": start_time_val
        }

        # LOG: Tayyorlangan paketni ko'rsatish
        log_as_table("2. HELPDESKEDDY UCHUN TAYYORLANGAN PACKET", payload)

        # 4. Yuborish (Execution)
        logger.info(f"🚀 HelpDeskEddy-ga ({HELPDESK_URL[-20:]}...) yuborilmoqda...")
        response = requests.post(HELPDESK_URL, json=payload, timeout=10)
        
        process_time = time.time() - start_time
        
        # LOG: Natijani ko'rsatish
        result_info = {
            "HTTP Code": response.status_code,
            "Response": response.text,
            "Time Taken": f"{process_time:.4f} seconds"
        }
        log_as_table("3. HELPDESKEDDY JAVOBI", result_info)

        return {
            "status": "success",
            "helpdesk_code": response.status_code,
            "processed_in": f"{process_time:.4f}s"
        }

    except Exception as e:
        # Xatolik bo'lsa to'liq ko'rsatish
        error_msg = traceback.format_exc()
        logger.error(f"\n❌ CRITICAL ERROR:\n{error_msg}")
        return {"status": "error", "message": str(e)}

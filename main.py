from fastapi import FastAPI, Request
import requests
import json
import logging

# Loglarni sozlash (xatolarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- SOZLAMALAR ---
# HelpDeskEddy Webhook manzili (Sizning skrinshotingizdan olindi)
HELPDESK_URL = "https://qwatt.helpdeskeddy.com/api/v2/telephony/calls/DyJmRuiZTsqsXyRsegJR"

@app.get("/")
def home():
    return {"status": "Binotel-HelpDeskEddy Middleware Ishlayapti!"}

@app.post("/webhook")
async def binotel_handler(request: Request):
    try:
        # 1. Binoteldan kelgan ma'lumotni olish
        # Binotel odatda form-data yuboradi, lekin ba'zida JSON bo'lishi mumkin
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            data = await request.json()
        else:
            form_data = await request.form()
            data = dict(form_data)
            # Agar Binotel ma'lumotni 'generalCallID' kabi ichki JSON qilib yuborsa:
            if 'requestType' not in data and len(data) == 1:
                # Ba'zan ma'lumot bitta kalit ichida JSON string bo'lib keladi
                key = list(data.keys())[0]
                try:
                    data = json.loads(key)
                except:
                    pass

        logger.info(f"Binoteldan kelgan ma'lumot: {data}")

        # 2. Ma'lumotlarni HelpDeskEddy formatiga o'tkazish
        # Sizning 3-skrinshotingizdagi strukturaga asoslanamiz
        
        # Binotelda ba'zi ma'lumotlar to'g'ridan-to'g'ri, ba'zilari massiv ichida bo'lishi mumkin.
        # Xavfsizlik uchun .get() ishlatamiz.
        
        external_number = data.get("externalNumber") # Mijoz raqami (99894...)
        internal_number = data.get("internalNumber") # Operator raqami (901)
        billsec = data.get("billsec", 0)             # Suhbat davomiyligi
        call_type_raw = data.get("callType", 0)      # 0 - kiruvchi, 1 - chiquvchi
        recording_url = data.get("linkToCallRecordInMyBusiness") # Audio link
        call_id = data.get("generalCallID")          # Unikal ID

        # Agar bu API CALL COMPLETED bo'lmasa, jarayonni to'xtatamiz
        if data.get("requestType") != "apiCallCompleted":
             return {"status": "ignored", "reason": "Not a completed call event"}

        # Call Type ni aniqlash
        # HelpDeskEddy uchun: 'inbound' yoki 'outbound'
        direction = "inbound"
        if str(call_type_raw) == "1":
            direction = "outbound"

        # Statusni aniqlash
        call_status = "missed"
        if int(billsec) > 0:
            call_status = "completed"

        # 3. HelpDeskEddy uchun tayyor payload
        payload = {
            "uuid": call_id,
            "type": direction,         # inbound/outbound
            "phone": external_number,  # Mijoz
            "extension": internal_number, # 901 (Bu orqali Diyora yoki Dilmurodga ticket ochiladi)
            "status": call_status,     # completed/missed
            "duration": billsec,
            "recording_url": recording_url,
            "timestamp": data.get("startTime")
        }

        logger.info(f"HelpDeskEddy-ga yuborilayotgan ma'lumot: {payload}")

        # 4. HelpDeskEddy-ga yuborish
        response = requests.post(HELPDESK_URL, json=payload, timeout=10)
        
        logger.info(f"HelpDeskEddy javobi: {response.status_code} - {response.text}")

        return {
            "status": "success",
            "helpdesk_code": response.status_code,
            "payload_sent": payload
        }

    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {str(e)}")
        return {"status": "error", "message": str(e)}

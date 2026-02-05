# 🚀 Connecter Middleware - Deploy va Setup Qo'llanmasi

## 📋 Mundarija
1. [Tizim Talablari](#tizim-talablari)
2. [Local Setup](#local-setup)
3. [Vercel Deploy](#vercel-deploy)
4. [Binotel Konfiguratsiya](#binotel-konfiguratsiya)
5. [Test Qilish](#test-qilish)
6. [Monitoring](#monitoring)

---

## 🔧 Tizim Talablari

- Python 3.9+
- Supabase account
- Vercel account (deploy uchun)
- Binotel API kalitlari
- HelpDeskEddy webhook URL

---

## 💻 Local Setup

### 1. Virtual Environment Yaratish

```bash
cd /Users/hazratqul/connecter
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# Windows: .venv\Scripts\activate
```

### 2. Dependencies O'rnatish

```bash
pip install -r backend/requirements.txt
```

### 3. Environment Variables

Backend papkasida `.env` file yarating:

```bash
cd backend
cp .env.example .env
```

`.env` faylini tahrirlang:

```env
# Supabase - Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key

# DEBUG MODE (local development uchun)
DEBUG_MODE=True
```

**MUHIM:** Qolgan API kalitlar `backend/src/core/config.py` da hardcoded!

### 4. Supabase Database Setup

Supabase da quyidagi tablitsalarni yarating:

```sql
-- 1. Customers jadvali
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    tags TEXT[],
    created_via VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Agents jadvali
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extension_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Calls jadvali
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    binotel_uuid VARCHAR(255) UNIQUE NOT NULL,
    direction VARCHAR(20),
    status VARCHAR(50),
    phone_number VARCHAR(50),
    agent_extension VARCHAR(20),
    agent_id UUID REFERENCES agents(id),
    customer_id UUID REFERENCES customers(id),
    duration_seconds INTEGER,
    recording_url TEXT,
    started_at TIMESTAMP,
    raw_payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Call enrichments jadvali (AI tahlil uchun)
CREATE TABLE call_enrichments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES calls(id) UNIQUE,
    transcription_text TEXT,
    summary TEXT,
    sentiment_score INTEGER,
    detected_topics TEXT[],
    action_items TEXT[],
    urgency_score INTEGER,
    key_points TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Webhook logs (debugging uchun)
CREATE TABLE webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payload JSONB,
    request_type VARCHAR(100),
    call_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5. Serverni Ishga Tushirish

```bash
cd backend
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Server ishga tushgach:
- Main: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Statistics: http://localhost:8000/stats

---

## 🌐 Vercel Deploy

### 1. Vercel CLI O'rnatish

```bash
npm install -g vercel
```

### 2. Loyihani Vercel ga Bog'lash

```bash
cd /Users/hazratqul/connecter
vercel login
vercel
```

### 3. Environment Variables Qo'shish

Vercel dashboard da yoki CLI orqali:

```bash
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY
```

Yoki Vercel dashboard: Settings → Environment Variables

### 4. Deploy Qilish

```bash
vercel --prod
```

Deploy tugagach, URL olinadi. Masalan:
```
https://connecter-middleware.vercel.app
```

### 5. Deploy Statusni Tekshirish

```bash
curl https://your-app.vercel.app/health
```

---

## 📞 Binotel Konfiguratsiya

### 1. Binotel Cabinet ga Kirish

1. https://my.binotel.ua ga kiring
2. Settings → Integrations → Webhooks

### 2. Webhook URL Qo'shish

**Production URL:**
```
https://your-app.vercel.app/webhook
```

**Local Test URL (ngrok orqali):**
```bash
# Terminal 1: Ngrok ishga tushiring
ngrok http 8000

# Ngrok bergan URL ni ishlating
https://abc123.ngrok.io/webhook
```

### 3. Qaysi Eventlarni Yuborish

Binotel settings da quyidagi eventlarni tanlang:
- ✅ `callCompleted` - Call tugaganda
- ✅ `incomingCallCompleted` - Kiruvchi call tugaganda
- ✅ `outgoingCallCompleted` - Chiquvchi call tugaganda

**MUHIM:** Boshqa eventlar (`callStarted`, `callAnswered`) middleware tomonidan ignore qilinadi.

### 4. Webhook Format

Binotel 2 xil formatda yuborishi mumkin:

**JSON Format:**
```json
{
  "generalCallID": "123456789",
  "requestType": "callCompleted",
  "direction": "incoming",
  "status": "ANSWER",
  "externalNumber": "+998901234567",
  "internalNumber": "101",
  "billsec": 180,
  "recordingUrl": "https://..."
}
```

**Form-Encoded Format:**
```
callDetails[generalCallID]=123456789
callDetails[requestType]=callCompleted
...
```

Middleware **ikkala formatni ham** qabul qiladi!

---

## 🧪 Test Qilish

### 1. Local Server Test

```bash
# Terminal 1: Server ishga tushiring
cd backend
python -m uvicorn src.api.main:app --reload

# Terminal 2: Test script ishga tushiring
python backend/test_webhook.py
```

### 2. Production Test

Test scriptni production URL ga qaratib ishga tushiring:

```python
# test_webhook.py da o'zgartiring:
SERVER_URL = "https://your-app.vercel.app/webhook"
```

```bash
python backend/test_webhook.py
```

### 3. Manual Test (curl)

```bash
curl -X POST https://your-app.vercel.app/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "generalCallID": "test_12345",
    "requestType": "callCompleted",
    "direction": "incoming",
    "status": "ANSWER",
    "externalNumber": "+998901234567",
    "internalNumber": "101",
    "billsec": 180
  }'
```

Expected response:
```json
{
  "status": "success",
  "message": "Call processing started",
  "call_id": "test_12345"
}
```

### 4. Real Binotel Test

1. Binotel dan real qo'ng'iroq qiling
2. Call tugagach, webhook avtomatik yuboriladi
3. Logs ni tekshiring:
   ```bash
   curl https://your-app.vercel.app/stats
   ```

---

## 📊 Monitoring

### 1. Dashboard

Browser da oching:
```
https://your-app.vercel.app/
```

Ko'rsatiladi:
- System status
- Total webhooks received/processed/errors
- Last webhook ma'lumoti

### 2. Statistics Endpoint

```bash
curl https://your-app.vercel.app/stats
```

Response:
```json
{
  "statistics": {
    "total_received": 150,
    "total_processed": 145,
    "total_ignored": 3,
    "total_errors": 2,
    "last_webhook_time": "2024-02-05 14:30:00",
    "last_call_id": "123456789"
  }
}
```

### 3. Supabase Logs

Supabase dashboard da:
1. Table Editor → `webhook_logs` - har bir webhookni ko'rish
2. Table Editor → `calls` - saqlangan calllar
3. Table Editor → `call_enrichments` - AI tahlil natijalari

### 4. Vercel Logs

Vercel dashboard:
- Deployments → Your Project → Logs
- Real-time logs va error traceback

---

## 🔍 Troubleshooting

### Webhook Qabul Qilinmayapti

**Tekshirish:**
```bash
# Health check
curl https://your-app.vercel.app/health

# Stats check
curl https://your-app.vercel.app/stats
```

**Sabablari:**
1. Binotel da noto'g'ri URL
2. Webhook event type noto'g'ri
3. Network blocking (firewall)

### HelpDeskEddy ga Yuborilmayapti

**Log tekshiring:**
- Vercel logs da "HelpDeskEddy" qidiring
- Error message ko'rish

**Sabablari:**
1. HelpDeskEddy URL noto'g'ri
2. Network timeout
3. HelpDeskEddy server ishlamayapti

### Database ga Saqlanmayapti

**Tekshirish:**
```bash
# Supabase connection test
curl https://your-app.vercel.app/health
```

**Sabablari:**
1. SUPABASE_URL yoki SUPABASE_KEY noto'g'ri
2. Supabase da tablitsalar yaratilmagan
3. RLS (Row Level Security) muammosi

**Fix:**
```sql
-- Supabase SQL Editor da:
ALTER TABLE customers DISABLE ROW LEVEL SECURITY;
ALTER TABLE agents DISABLE ROW LEVEL SECURITY;
ALTER TABLE calls DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_enrichments DISABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_logs DISABLE ROW LEVEL SECURITY;
```

### AI Processing Ishlamayapti

**Sabablari:**
1. OpenAI API key noto'g'ri yoki limit tugagan
2. Recording URL accessible emas
3. Audio file juda katta (>25MB)

**Tekshirish:**
- OpenAI dashboard: https://platform.openai.com/usage
- Balance va limit ko'rish

---

## 📚 API Endpoints Reference

### POST /webhook
**Maqsad:** Binotel dan webhook qabul qilish

**Request:**
```json
{
  "generalCallID": "string",
  "requestType": "callCompleted",
  "direction": "incoming|outgoing",
  "status": "ANSWER|NOANSWER|BUSY|...",
  "externalNumber": "+998901234567",
  "internalNumber": "101",
  "billsec": 180,
  "recordingUrl": "https://..."
}
```

**Response:**
```json
{
  "status": "success|ignored|error",
  "message": "string",
  "call_id": "string"
}
```

### GET /
**Maqsad:** System dashboard (HTML)

### GET /health
**Maqsad:** Health check

**Response:**
```json
{
  "status": "healthy",
  "service": "Connecter Middleware v2.0",
  "version": "2.0.0",
  "timestamp": "2024-02-05T14:30:00+05:00"
}
```

### GET /stats
**Maqsad:** Processing statistics

**Response:**
```json
{
  "statistics": {
    "total_received": 0,
    "total_processed": 0,
    "total_ignored": 0,
    "total_errors": 0,
    "last_webhook_time": null
  },
  "timestamp": "2024-02-05T14:30:00+05:00"
}
```

### GET /docs
**Maqsad:** Interactive API documentation (Swagger UI)

---

## 🔐 Security Best Practices

### Production uchun

1. **CORS ni cheklang:**
```python
# src/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # * o'rniga
    ...
)
```

2. **Rate Limiting qo'shing:**
```bash
pip install slowapi
```

3. **Webhook Signature Validation:**
Binotel signature yuborsa, uni tekshiring.

4. **Environment Variables:**
Hech qachon API kalitlarni code ga commit qilmang!

---

## 📞 Yordam

Muammo yuzaga kelsa:

1. **Logs ni tekshiring:**
   - Vercel: Deployments → Logs
   - Supabase: Logs → API Logs

2. **Test script ishga tushiring:**
   ```bash
   python backend/test_webhook.py
   ```

3. **GitHub Issues ochish:**
   - Repository: https://github.com/your-repo/connecter
   - Issue yarating va error log qo'shing

---

## 📝 Version History

- **v2.0.0** - Production-ready refactor
- **v1.0.0** - Initial implementation

---

## ✅ Checklist Deploy Uchun

- [ ] Python 3.9+ o'rnatilgan
- [ ] Virtual environment yaratilgan
- [ ] Dependencies o'rnatilgan
- [ ] Supabase account yaratilgan
- [ ] Supabase da tablitsalar yaratilgan
- [ ] `.env` file yaratilgan va to'ldirilgan
- [ ] Local server test qilindi
- [ ] Vercel account yaratilgan
- [ ] Vercel ga deploy qilindi
- [ ] Vercel da environment variables qo'shildi
- [ ] Binotel da webhook URL sozlandi
- [ ] Production test qilindi (real call)
- [ ] HelpDeskEddy da call ko'rindi
- [ ] Supabase da ma'lumot saqlandi

---

**Muvaffaqiyatli Deploy! 🎉**

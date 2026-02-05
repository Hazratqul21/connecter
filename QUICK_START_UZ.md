# 🚀 Connecter Middleware - Qisqa Qo'llanma (O'zbekcha)

## 📱 Nima qiladi?

Bu middleware **Binotel** (telefon tizimi) va **HelpDeskEddy** (CRM) ni bog'laydi.

**Ishlovchi jarayon:**
1. Binotel dan qo'ng'iroq tugadi → webhook keladi
2. Middleware qabul qiladi va 3 ta ish bajaradi:
   - ✅ HelpDeskEddy ga yuboradi (CRM ga kiradi)
   - ✅ Supabase databasega saqlaydi
   - ✅ AI bilan audio transkript va tahlil qiladi

---

## 🛠️ Tez Setup (5 daqiqa)

### 1. Supabase Setup

1. https://supabase.com ga boring
2. Yangi project yarating
3. SQL Editor da `DEPLOYMENT_GUIDE.md` dagi SQL scriptlarni ishga tushiring
4. Settings → API da `URL` va `service_role key` ni oling

### 2. Local Test

```bash
# 1. Virtual environment
cd /Users/hazratqul/connecter
python3 -m venv .venv
source .venv/bin/activate

# 2. Dependencies
pip install -r backend/requirements.txt

# 3. Environment variables
cd backend
cp .env.example .env
# .env ni tahrirlang: SUPABASE_URL va SUPABASE_KEY

# 4. Server ishga tushiring
python -m uvicorn src.api.main:app --reload

# 5. Test qiling
python test_webhook.py
```

### 3. Vercel Deploy

```bash
# Vercel CLI o'rnating
npm install -g vercel

# Login va deploy
vercel login
cd /Users/hazratqul/connecter
vercel

# Environment variables qo'shing
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY

# Production deploy
vercel --prod
```

### 4. Binotel Sozlash

1. https://my.binotel.ua → Settings → Webhooks
2. URL: `https://your-app.vercel.app/webhook`
3. Events:
   - ✅ callCompleted
   - ✅ incomingCallCompleted
   - ✅ outgoingCallCompleted

---

## 🔍 Tekshirish

### Health Check
```bash
curl https://your-app.vercel.app/health
```

### Statistika
```bash
curl https://your-app.vercel.app/stats
```

### Dashboard
Browser da: `https://your-app.vercel.app/`

---

## 🎯 API Kalitlar (Hardcoded)

**Hamma kalitlar `backend/src/core/config.py` da:**

```python
BINOTEL_API_KEY = "70206a-84faf4d"
BINOTEL_API_SECRET = "e4a051-9d3c02-7cdb1a-a5d224-f8406eda"
HELPDESKEDDY_URL = "https://qwatt.helpdeskeddy.com/api/v2/telephony/calls/..."
OPENAI_API_KEY = "sk-proj-..."
```

**Faqat Supabase environment variable:**
- `SUPABASE_URL`
- `SUPABASE_KEY`

---

## 📊 Database Struktura

5 ta jadval:
1. **customers** - mijozlar (telefon raqam bo'yicha)
2. **agents** - agentlar (extension number bo'yicha)
3. **calls** - barcha qo'ng'iroqlar
4. **call_enrichments** - AI tahlil (transkripsiya, sentiment)
5. **webhook_logs** - debug uchun

---

## 🐛 Muammolar

### Webhook kelmayapti?
- Binotel URL ni tekshiring
- Health check qiling: `/health`

### HelpDeskEddy ga ketmayapti?
- Vercel logs ko'ring
- URL to'g'ri ekanligini tekshiring

### Database ga saqlanmayapti?
- `.env` da SUPABASE kalitlarni tekshiring
- Supabase da tablitsalar borligini tekshiring

### AI ishlamayapti?
- OpenAI API key limitni tekshiring
- Recording URL accessible ekanligini tekshiring

---

## 📞 Test Qilish

**Real test:**
1. Binotel dan qo'ng'iroq qiling
2. `/stats` endpoint ni tekshiring
3. Supabase da `calls` jadvalini ko'ring
4. HelpDeskEddy da qo'ng'iroq paydo bo'ldi mi?

**Manual test:**
```bash
python backend/test_webhook.py
```

---

## ✅ Tayyor!

Middleware ishga tushdi. Har bir qo'ng'iroq:
1. ✅ HelpDeskEddy ga boradi
2. ✅ Database ga saqlanadi
3. ✅ AI tahlil qilinadi (agar recording bo'lsa)

Monitoring: `https://your-app.vercel.app/` dashboard

Muammo bo'lsa: `DEPLOYMENT_GUIDE.md` ni o'qing (to'liq qo'llanma).

---

**Muvaffaqiyatli! 🎉**

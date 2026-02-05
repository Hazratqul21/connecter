#!/bin/bash
# Connecter Middleware - Quick Setup Script
# Bu script loyihani tez setup qiladi

echo "🚀 Connecter Middleware - Setup Script"
echo "======================================"

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 topilmadi! Avval Python 3.9+ o'rnating."
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "   ✅ Virtual environment yaratildi"
else
    echo "   ℹ️  Virtual environment allaqachon mavjud"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source .venv/bin/activate
echo "   ✅ Virtual environment activated"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt
echo "   ✅ Dependencies o'rnatildi"

# Create .env file if not exists
echo ""
echo "⚙️  Setting up environment variables..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "   ✅ .env file yaratildi (backend/.env.example dan)"
    echo ""
    echo "   ⚠️  MUHIM: backend/.env faylini tahrirlang va Supabase credentials qo'shing:"
    echo "      - SUPABASE_URL"
    echo "      - SUPABASE_KEY"
    echo ""
else
    echo "   ℹ️  .env file allaqachon mavjud"
fi

# Check if Supabase credentials are set
echo ""
echo "🔍 Checking Supabase credentials..."
if grep -q "your_supabase_url" backend/.env || grep -q "your_supabase_service_role_key" backend/.env; then
    echo "   ⚠️  Supabase credentials hali sozlanmagan!"
    echo "      backend/.env ni tahrirlang va to'g'ri credentials kiriting."
else
    echo "   ✅ Supabase credentials set"
fi

echo ""
echo "======================================"
echo "✅ Setup tugadi!"
echo ""
echo "📝 Keyingi qadamlar:"
echo ""
echo "1. Supabase setup (agar qilmagan bo'lsangiz):"
echo "   - https://supabase.com da project yarating"
echo "   - SQL Editor da tablitsalarni yarating (DEPLOYMENT_GUIDE.md ga qarang)"
echo "   - API credentials ni backend/.env ga qo'shing"
echo ""
echo "2. Server ishga tushiring:"
echo "   cd backend"
echo "   python -m uvicorn src.api.main:app --reload"
echo ""
echo "3. Test qiling:"
echo "   python backend/test_webhook.py"
echo ""
echo "4. Deploy qiling (Vercel):"
echo "   npm install -g vercel"
echo "   vercel --prod"
echo ""
echo "📚 To'liq qo'llanma: DEPLOYMENT_GUIDE.md"
echo "🚀 Qisqa qo'llanma: QUICK_START_UZ.md"
echo ""

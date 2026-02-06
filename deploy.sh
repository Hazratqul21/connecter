#!/bin/bash

# Vercel Deploy Script
# Bu script loyihani Vercel ga deploy qiladi

echo "🚀 Vercel Deploy Script"
echo "======================"

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI topilmadi!"
    echo "   O'rnatish: npm install -g vercel"
    exit 1
fi

echo "✅ Vercel CLI topildi"
echo ""

# Show current configuration
echo "📋 Hozirgi konfiguratsiya:"
echo "   - Root: $(pwd)"
echo "   - Entry point: api/index.py"
echo "   - Backend: backend/src/api/main.py"
echo ""

# Check if user is logged in
echo "🔐 Vercel login tekshirilmoqda..."
vercel whoami 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Vercel ga login qilmagan"
    echo "   Login qiling: vercel login"
    exit 1
fi

echo "✅ Login successful"
echo ""

# Environment variables reminder
echo "⚠️  Environment Variables:"
echo "   Vercel dashboard da quyidagilarni qo'shganingizni tekshiring:"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_KEY"
echo ""
read -p "Environment variables sozlangan? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo ""
    echo "Avval environment variables qo'shing:"
    echo "1. Vercel dashboard ga o'ting"
    echo "2. Project → Settings → Environment Variables"
    echo "3. Qo'shing:"
    echo "   SUPABASE_URL = your_supabase_url"
    echo "   SUPABASE_KEY = your_supabase_key"
    echo ""
    exit 0
fi

# Deploy
echo ""
echo "🚀 Deploying to production..."
vercel --prod

echo ""
echo "✅ Deploy tugadi!"
echo ""
echo "📝 Keyingi qadamlar:"
echo "1. Vercel URL ni oling (yuqorida ko'rsatilgan)"
echo "2. Binotel da webhook URL ni sozlang"
echo "3. Test qiling: curl https://your-url.vercel.app/health"
echo ""

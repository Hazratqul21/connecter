#!/usr/bin/env python3
"""
Binotel Webhook Test Script
Binotel dan kelgan webhook ni local yoki production serverga test qilish uchun
"""
import requests
import json
from datetime import datetime

# Test uchun server URL (local yoki production)
SERVER_URL = "http://localhost:8000/webhook"
# SERVER_URL = "https://your-vercel-app.vercel.app/webhook"

# Binotel dan kelgan webhook simulatsiyasi
def test_incoming_call_completed():
    """Incoming call completed webhook test"""
    payload = {
        "generalCallID": "test_123456789",
        "requestType": "incomingCallCompleted",
        "direction": "incoming",
        "status": "ANSWER",
        "externalNumber": "+998901234567",
        "internalNumber": "101",
        "billsec": 180,
        "recordingUrl": "https://example.com/recordings/test.mp3",
        "linkToCallRecordInMyBusiness": "https://example.com/records/test"
    }
    
    print("=" * 60)
    print("📞 Testing INCOMING call webhook...")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            SERVER_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_outgoing_call_completed():
    """Outgoing call completed webhook test"""
    payload = {
        "generalCallID": "test_987654321",
        "requestType": "outgoingCallCompleted",
        "direction": "outgoing",
        "status": "ANSWER",
        "externalNumber": "+998901234567",
        "internalNumber": "102",
        "billsec": 240,
        "recordingUrl": "https://example.com/recordings/test2.mp3"
    }
    
    print("\n" + "=" * 60)
    print("📞 Testing OUTGOING call webhook...")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            SERVER_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_invalid_event_type():
    """Invalid event type - should be ignored"""
    payload = {
        "generalCallID": "test_invalid",
        "requestType": "callStarted",  # Bu event type ignore qilinadi
        "direction": "incoming",
        "status": "RINGING"
    }
    
    print("\n" + "=" * 60)
    print("🚫 Testing INVALID event type (should be ignored)...")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            SERVER_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def test_form_encoded_webhook():
    """Test form-encoded webhook (Binotel alternative format)"""
    payload = {
        "callDetails[generalCallID]": "test_form_123",
        "callDetails[requestType]": "callCompleted",
        "callDetails[direction]": "incoming",
        "callDetails[externalNumber]": "+998901234567",
        "callDetails[internalNumber]": "103",
        "callDetails[billsec]": "150"
    }
    
    print("\n" + "=" * 60)
    print("📝 Testing FORM-ENCODED webhook...")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            SERVER_URL,
            data=payload,  # data= ni ishlatamiz (form-encoded)
            timeout=10
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")


def check_server_health():
    """Server health check"""
    try:
        health_url = SERVER_URL.replace("/webhook", "/health")
        response = requests.get(health_url, timeout=5)
        
        print("\n" + "=" * 60)
        print("💚 Server Health Check")
        print("=" * 60)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Server not accessible: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 Connecter Middleware - Webhook Test Suite")
    print(f"🎯 Target Server: {SERVER_URL}")
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Avval server health check
    if not check_server_health():
        print("\n⚠️  Server ishlamayapti. Avval serverni ishga tushiring:")
        print("   cd backend && python -m uvicorn src.api.main:app --reload")
        exit(1)
    
    # Test suiteni ishga tushirish
    test_incoming_call_completed()
    test_outgoing_call_completed()
    test_invalid_event_type()
    test_form_encoded_webhook()
    
    print("\n" + "=" * 60)
    print("✅ Test Suite Completed!")
    print("=" * 60)
    print("\n📊 Statistikani ko'rish uchun:")
    print(f"   curl {SERVER_URL.replace('/webhook', '/stats')}")
    print("\n")

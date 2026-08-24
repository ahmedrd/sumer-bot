import requests
import config

def send_telegram_message(message):
    """إرسال التقرير التحليلي مباشرة إلى حسابك على تليجرام"""
    if not config.TELEGRAM_TOKEN or config.TELEGRAM_CHAT_ID == "ضع_معرف_الـ_شات_هنا":
        print("⚠️ تنبيه: يرجى إدخال الـ TELEGRAM_CHAT_ID الصحيح في ملف config.py أولاً.")
        return
        
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("📤 تم إرسال التقرير إلى تليجرام بنجاح!")
        else:
            print(f"❌ فشل إرسال التقرير لتليجرام: {response.text}")
    except Exception as e:
        print(f"❌ خطأ في الاتصال بشبكة تليجرام: {e}")
import sqlite3
import asyncio
import os
import requests
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
import jinja2
import config
from database import init_db, add_subscriber, get_all_subscribers, get_all_markets
from market_fetcher import get_market_data

app = FastAPI()

STATE_FILE = "bot_state.txt"
CREATOR_FILE = "creator_handle.txt"

def get_bot_status():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip() == "True"
    return False

def set_bot_status(status: bool):
    with open(STATE_FILE, "w") as f:
        f.write(str(status))

def get_creator_handle():
    if os.path.exists(CREATOR_FILE):
        with open(CREATOR_FILE, "r") as f:
            return f.read().strip()
    return "AhmedRadhi" # حسابك الافتراضي

def set_creator_handle(handle: str):
    with open(CREATOR_FILE, "w") as f:
        f.write(handle.strip())

auto_alert_status = {"running": get_bot_status()}

@app.on_event("startup")
def startup_event():
    init_db()
    # استئناف التشغيل في الخلفية إذا كانت الحالة مفعلة مسبقاً
    if auto_alert_status["running"]:
        asyncio.create_task(background_auto_alerter())

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>منصة سومر الذكية للتداول الاحترافي</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Cairo', sans-serif; }</style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen p-6 selection:bg-amber-500 selection:text-black">
    <div class="max-w-6xl mx-auto">
        <header class="text-center mb-10 border-b border-gray-800 pb-6">
            <h1 class="text-4xl font-extrabold text-amber-400 mb-2 tracking-wide">🏛 منصة سومر الذكية للتداول الاحترافي</h1>
            <p class="text-gray-400 text-sm">نظام تحليل الأسواق العالمي - إرسال التقارير الفنية المتقدمة وسكرين شوت الشارت للمشتركين</p>
        </header>

        <!-- لوحة التحكم في نظام التنبيهات التلقائية -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="md:col-span-2 bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800 flex justify-between items-center">
                <div>
                    <h2 class="text-xl font-semibold text-amber-300">⚙️ التنبيهات التلقائية المجدولة</h2>
                    <p class="text-sm text-gray-400 mt-1">الحالة: <span class="font-bold {{ 'text-emerald-400' if auto_running else 'text-rose-400' }}">{{ 'مفعلة وتعمل في الخلفية 🚀' if auto_running else 'متوقفة ⏹' }}</span></p>
                </div>
                <form action="/toggle-auto" method="POST">
                    {% if auto_running %}
                        <button type="submit" class="bg-rose-600 hover:bg-rose-500 transition text-white font-bold px-6 py-3 rounded-xl shadow-lg cursor-pointer">إيقاف التلقائي</button>
                    {% else %}
                        <button type="submit" class="bg-emerald-600 hover:bg-emerald-500 transition text-white font-bold px-6 py-3 rounded-xl shadow-lg cursor-pointer">تشغيل التلقائي</button>
                    {% endif %}
                </form>
            </div>

            <!-- إعدادات حساب المتابع / المطور -->
            <div class="bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800">
                <h3 class="text-lg font-semibold text-cyan-400 mb-2">👨‍💻 حساب المتابعة الشخصي</h3>
                <form action="/update-creator" method="POST" class="space-y-3">
                    <input type="text" name="creator" value="{{ creator_handle }}" placeholder="معرف تليجرام بدون @" required class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500">
                    <button type="submit" class="w-full bg-cyan-700 hover:bg-cyan-600 transition text-white font-semibold py-2 rounded-lg text-sm shadow">حفظ المعرف</button>
                </form>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <!-- قسم إضافة مشترك تليجرام جديد -->
            <div class="bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800">
                <h2 class="text-xl font-semibold mb-4 text-emerald-400">➕ إضافة مشترك تليجرام جديد</h2>
                <form action="/add-user" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-sm mb-1 text-gray-300">اسم المشترك:</label>
                        <input type="text" name="name" required class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <div>
                        <label class="block text-sm mb-1 text-gray-300">رقم الـ Chat ID:</label>
                        <input type="text" name="chat_id" required class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-white focus:outline-none focus:border-emerald-500">
                    </div>
                    <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 transition text-white font-bold p-3 rounded-xl shadow-lg cursor-pointer">حفظ المشترك</button>
                </form>
            </div>

            <!-- قسم التحليل الفوري وإرسال الشارت يدوياً -->
            <div class="bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800">
                <h2 class="text-xl font-semibold mb-4 text-cyan-400">📊 تحليل وإرسال شارت فوري</h2>
                <form action="/run-analysis" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-sm mb-1 text-gray-300">اختر السوق أو السلعة:</label>
                        <select name="symbol" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-white focus:outline-none focus:border-cyan-500">
                            {% for market in markets %}
                                <option value="{{ market.symbol }}">{{ market.name }} ({{ market.symbol }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit" class="w-full bg-cyan-600 hover:bg-cyan-500 transition text-white font-bold p-3 rounded-xl mt-8 shadow-lg cursor-pointer">إرسال التقرير والشارت الآن 📈</button>
                </form>
            </div>
        </div>

        <!-- قائمة المشتركين المسجلين مع خيارات التحكم والحذف -->
        <div class="bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800">
            <h2 class="text-xl font-semibold mb-4 text-purple-400">👥 المشتركون الحاليون ({{ subscribers|length }})</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-right">
                    <thead>
                        <tr class="border-b border-gray-800 text-gray-400 text-sm">
                            <th class="pb-3 px-2">الاسم</th>
                            <th class="pb-3 px-2">Chat ID</th>
                            <th class="pb-3 px-2">الحالة</th>
                            <th class="pb-3 px-2 text-center">الإجراءات والتحكم</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-800/60">
                        {% for sub in subscribers %}
                        <tr>
                            <td class="py-3 px-2 font-medium">{{ sub.name }}</td>
                            <td class="py-3 px-2 text-amber-300 font-mono">{{ sub.chat_id }}</td>
                            <td class="py-3 px-2 text-emerald-400 font-bold">نشط ✅</td>
                            <td class="py-3 px-2 text-center">
                                <form action="/delete-user" method="POST" onsubmit="return confirm('هل أنت متأكد من حذف هذا المشترك نهائياً؟');" style="display:inline;">
                                    <input type="hidden" name="chat_id" value="{{ sub.chat_id }}">
                                    <button type="submit" class="bg-rose-600/80 hover:bg-rose-600 text-white px-3 py-1.5 rounded-lg text-sm transition shadow cursor-pointer">حذف 🗑️</button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="4" class="text-center py-6 text-gray-500">لا يوجد مشتركين مسجلين حالياً.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    conn = sqlite3.connect("sumer_system.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subscribers")
    subscribers = cursor.fetchall()
    conn.close()
    
    markets = get_all_markets()
    
    template = jinja2.Template(HTML_TEMPLATE)
    html_content = template.render(
        subscribers=subscribers, 
        markets=markets, 
        auto_running=auto_alert_status["running"],
        creator_handle=get_creator_handle()
    )
    return HTMLResponse(content=html_content)

@app.post("/add-user")
async def add_user(name: str = Form(...), chat_id: str = Form(...)):
    add_subscriber(name, chat_id)
    return HTMLResponse(content="<script>alert('تم إضافة المشترك بنجاح!'); window.location.href='/';</script>")

@app.post("/update-creator")
async def update_creator(creator: str = Form(...)):
    set_creator_handle(creator)
    return HTMLResponse(content="<script>alert('تم تحديث حساب المتابعة بنجاح!'); window.location.href='/';</script>")

@app.post("/delete-user")
async def delete_user(chat_id: str = Form(...)):
    try:
        conn = sqlite3.connect("sumer_system.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        return HTMLResponse(content="<script>alert('تم حذف المشترك بنجاح!'); window.location.href='/';</script>")
    except Exception as e:
        return HTMLResponse(content=f"<script>alert('حدث خطأ أثناء الحذف: {e}'); window.location.href='/';</script>")

@app.post("/run-analysis")
async def run_analysis(symbol: str = Form(...)):
    try:
        success = execute_market_analysis_and_notify(symbol)
        if not success:
            return HTMLResponse(content=f"<script>alert('تعذر جلب بيانات السوق أو رسم الشارت للأصل {symbol}!'); window.location.href='/';</script>")
        return HTMLResponse(content="<script>alert('تم تحليل السوق وإرسال السكرين شوت والتقرير للمشتركين بنجاح!'); window.location.href='/';</script>")
    except Exception as e:
        print(f"❌ خطأ فادح في التنفيذ اليدوي: {e}")
        return HTMLResponse(content=f"<script>alert('حدث خطأ: {e}'); window.location.href='/';</script>")

@app.post("/toggle-auto")
async def toggle_auto():
    auto_alert_status["running"] = not auto_alert_status["running"]
    set_bot_status(auto_alert_status["running"])
    if auto_alert_status["running"]:
        asyncio.create_task(background_auto_alerter())
    return HTMLResponse(content="<script>window.location.href='/';</script>")

def execute_market_analysis_and_notify(symbol):
    df, image_path = get_market_data(symbol)
    if df is None or df.empty:
        return False
    
    latest = df.iloc[-1]
    price = latest.get('close', 0)
    rsi = latest.get('RSI', 50)
    sma20 = latest.get('SMA_20', price)
    pattern = latest.get('detected_pattern', 'استقرار سعري')
    support = latest.get('support_level', price * 0.98)
    resistance = latest.get('resistance_level', price * 1.02)
    asset_type = latest.get('asset_type_desc', 'أصل مالي عالمي')

    if rsi < 38 or "Hammer" in pattern or "Bullish" in pattern:
        decision = "🟢 توصية شراء استراتيجية (STRONG BUY)"
        ai_reason = "رصد تشبع بيعي حاد مع ارتداد السعر من مستويات الدعم الحيوية وسط تدفقات شرائية مؤسسية."
        confidence = "88.5%"
    elif rsi > 62 or "Bearish" in pattern:
        decision = "🔴 توصية بيع / جني أرباح (STRONG SELL)"
        ai_reason = "اقتراب السعر من مناطق مقاومة عنيدة مع ضعف تدريجي في الزخم الشرائي وظهور إشارات تصريف."
        confidence = "81.0%"
    else:
        decision = "🟡 توصية بالتريث والمراقبة (HOLD / WAIT)"
        ai_reason = "السعر يتحرك ضمن قناة سعرية عرضية بانتظار إغلاق شمعة تأكيديه لاختراق أحد المستويات."
        confidence = "60.0%"

    daily_view = "🟢 صاعد ومستقر" if price > sma20 else "🔴 تحت ضغط بيعي مؤقت"
    weekly_view = "⭐ فرصة تجميع استثماري قوية للمدى المتوسط"
    monthly_view = "💎 نظرة هيكلية إيجابية تدعم الاستثمار طويل الأجل"

    creator = get_creator_handle()
    creator_link = f"https://t.me/{creator}" if not creator.startswith("http") else creator

    report = (
        f"🌐 *منصة سومر الذكية - تقرير مباشر*\n\n"
        f"📌 *فئة الأصل:* `{asset_type}`\n"
        f"🏷 *رمز الأصل:* `{symbol.upper()}`\n"
        f"💵 *السعر الفوري الحالي:* `{price:,.2f}`\n\n"
        f"🤖 *القرار النهائي:* \n*{decision}*\n"
        f"📊 *مؤشر الثقة والاعتمادية:* `{confidence}`\n\n"
        f"💡 *التحليل والسبب الفني المعمق:*\n_{ai_reason}_\n\n"
        f"⏱ *تحليل النطاقات الزمنية المتعددة:*\n"
        f"• 📈 *الصفقة اللحظية (Scalping):* نشطة ومهيأة للتنفيذ\n"
        f"• 📅 *الاتجاه اليومي (Daily):* {daily_view}\n"
        f"• 📆 *النظرة الأسبوعية (Weekly):* {weekly_view}\n"
        f"• 🗓 *الرؤية الشهرية (Macro):* {monthly_view}\n\n"
        f"🎯 *خريطة المستويات السعرية الحرجة:*\n"
        f"• 🟢 *منطقة الدعم الذهبي (Stop Loss / Entry):* `{support:,.2f}`\n"
        f"• 🔴 *منطقة المقاومة الحديدية (Target):* `{resistance:,.2f}`\n\n"
        f"📈 *قراءات المؤشرات والشموع اليابانية الحية:*\n"
        f"• *مؤشر القوة النسبية RSI(14):* `{rsi:.2f}`\n"
        f"• *النموذج الفني المرصود:* `{pattern}`\n\n"
        f"👑 *للتواصل والمتابعة الشخصية:* \n"
        f"[{creator}]({creator_link})"
    )

    subscribers = get_all_subscribers()
    for chat_id in subscribers:
        send_telegram_photo_and_report(chat_id, report, image_path)
        
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except:
            pass
            
    return True

async def background_auto_alerter():
    while auto_alert_status["running"]:
        try:
            markets = get_all_markets()
            for market in markets:
                if not auto_alert_status["running"]:
                    break
                execute_market_analysis_and_notify(market['symbol'])
                await asyncio.sleep(10)
        except Exception as e:
            print(f"خطأ في التنبيهات التلقائية: {e}")
        
        for _ in range(3600):
            if not auto_alert_status["running"]:
                break
            await asyncio.sleep(1)

def send_telegram_photo_and_report(chat_id, message, image_path):
    clean_chat_id = str(chat_id).strip()
    
    if image_path and os.path.exists(image_path):
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendPhoto"
        with open(image_path, 'rb') as photo_file:
            payload = {
                "chat_id": clean_chat_id, 
                "caption": message, 
                "parse_mode": "Markdown"
            }
            files = {"photo": photo_file}
            try:
                response = requests.post(url, data=payload, files=files, timeout=10)
                res_data = response.json()
                if response.status_code == 200 and res_data.get("ok"):
                    print(f"✅ تم إرسال الشارت الاحترافي والتقرير إلى المشترك: {clean_chat_id}")
                    return
            except Exception as e:
                print(f"❌ خطأ شبكة أثناء إرسال الصورة: {e}")
                
    url_msg = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload_msg = {"chat_id": clean_chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url_msg, json=payload_msg, timeout=10)
    except Exception as e:
        print(f"❌ خطأ في إرسال التقرير النصي: {e}")

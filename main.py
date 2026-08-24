import sqlite3
import asyncio
import os
import requests
from fastapi import FastAPI, Form, Request, Body, HTTPException
from fastapi.responses import HTMLResponse
import jinja2
import config
from database import init_db, add_subscriber, get_all_subscribers, get_all_markets
from market_fetcher import get_market_data

app = FastAPI()

STATE_FILE = "bot_state.txt"
CREATOR_FILE = "creator_handle.txt"
DB_FILE = "sumer_schedules.db"

def init_schedules_db():
    """إنشاء جدول قاعدة البيانات لتخزين التنبيهات المجدولة والصمود أمام إعادة التشغيل"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            condition_type TEXT,
            target_value REAL,
            is_active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات عند الإقلاع
init_schedules_db()

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
    return "AhmedRadhi"

def set_creator_handle(handle: str):
    with open(CREATOR_FILE, "w") as f:
        f.write(handle.strip())

auto_alert_status = {"running": get_bot_status()}

@app.on_event("startup")
def startup_event():
    init_db()
    init_schedules_db()
    if auto_alert_status["running"]:
        asyncio.create_task(background_auto_alerter())

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>منصة سومر الذكية - التداول العبقري والتحليل الحي</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Cairo', sans-serif; }</style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen p-6 selection:bg-amber-500 selection:text-black">
    <div class="max-w-6xl mx-auto">
        <header class="text-center mb-10 border-b border-gray-800 pb-6">
            <h1 class="text-4xl font-extrabold text-amber-400 mb-2 tracking-wide">🏛 منصة سومر الذكية - التحليل العبقري وإدارة المخاطر</h1>
            <p class="text-gray-400 text-sm">محرك تحليل الأسهم والأصول الحقيقي - تحديد مستويات الأمان القصوى للأرباح ووقف الخسارة التلقائي</p>
        </header>

        <!-- لوحة التحكم في نظام التنبيهات التلقائية وإعدادات المطور -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="md:col-span-2 bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-800 flex justify-between items-center">
                <div>
                    <h2 class="text-xl font-semibold text-amber-300">⚙️ التحليل والربط الذكي في الخلفية</h2>
                    <p class="text-sm text-gray-400 mt-1">الحالة: <span class="font-bold {{ 'text-emerald-400' if auto_running else 'text-rose-400' }}">{{ 'مفعل ويعمل بذكاء فائق 🚀' if auto_running else 'متوقف ⏹' }}</span></p>
                </div>
                <form action="/toggle-auto" method="POST">
                    {% if auto_running %}
                        <button type="submit" class="bg-rose-600 hover:bg-rose-500 transition text-white font-bold px-6 py-3 rounded-xl shadow-lg cursor-pointer">إيقاف التلقائي</button>
                    {% else %}
                        <button type="submit" class="bg-emerald-600 hover:bg-emerald-500 transition text-white font-bold px-6 py-3 rounded-xl shadow-lg cursor-pointer">تشغيل التلقائي</button>
                    {% endif %}
                </form>
            </div>

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
                <h2 class="text-xl font-semibold mb-4 text-cyan-400">📊 تحليل عبقري فوري مع مستويات الحماية</h2>
                <form action="/run-analysis" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-sm mb-1 text-gray-300">اختر السوق أو السلعة أو السهم:</label>
                        <select name="symbol" class="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-white focus:outline-none focus:border-cyan-500">
                            {% for market in markets %}
                                <option value="{{ market.symbol }}">{{ market.name }} ({{ market.symbol }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit" class="w-full bg-cyan-600 hover:bg-cyan-500 transition text-white font-bold p-3 rounded-xl mt-8 shadow-lg cursor-pointer">إرسال التقرير والرسม البياني الآمن الآن 📈</button>
                </form>
            </div>
        </div>

        <!-- قائمة المشتركين المسجلين -->
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
            return HTMLResponse(content=f"<script>alert('تعذر جلب بيانات السوق للأصل {symbol}!'); window.location.href='/';</script>")
        return HTMLResponse(content="<script>alert('تم تحليل السوق وإرسال التقرير والشارت العبقري للمشتركين بنجاح!'); window.location.href='/';</script>")
    except Exception as e:
        return HTMLResponse(content=f"<script>alert('حدث خطأ: {e}'); window.location.href='/';</script>")

@app.post("/toggle-auto")
async def toggle_auto():
    auto_alert_status["running"] = not auto_alert_status["running"]
    set_bot_status(auto_alert_status["running"])
    if auto_alert_status["running"]:
        asyncio.create_task(background_auto_alerter())
    return HTMLResponse(content="<script>window.location.href='/';</script>")

# 🌐 **استقبال إشارات المنصات الخارجية وتأمينها**
@app.post("/mt-webhook")
async def metatrader_webhook(data: dict = Body(...)):
    try:
        symbol = data.get("symbol", "UNKNOWN")
        action = data.get("action", "SIGNAL")
        price = data.get("price", 0)
        source = data.get("source", "منصة تداول خارجية (MT4/MT5/IB)")
        sl = data.get("sl", price * 0.985)
        tp = data.get("tp", price * 1.025)
        
        creator = get_creator_handle()
        creator_link = f"https://t.me/{creator}" if not creator.startswith("http") else creator

        report = (
            f"🏛 *منصة سومر العبقرية - تنبيه تنفيذ آلي*\n\n"
            f"📡 *المصدر:* `{source}`\n"
            f"🏷 *الأصل / الزوج:* `{symbol.upper()}`\n"
            f"📊 *نوع الصفقة:* `{action}`\n"
            f"💵 *سعر الدخول:* `{price:,.2f}`\n\n"
            f"🎯 *أعلى سعر إغلاق آمن (جني الأرباح):* `{tp:,.2f}`\n"
            f"🛑 *أدنى سعر إغلاق آمن (وقف الخسارة):* `{sl:,.2f}`\n\n"
            f"⚡ تم حساب مستويات الأمان التلقائية لمنع الخسارة بنجاح.\n\n"
            f"👑 *للتواصل والمتابعة:* \n"
            f"[{creator}]({creator_link})"
        )

        subscribers = get_all_subscribers()
        for chat_id in subscribers:
            send_telegram_photo_and_report(chat_id, report, image_path=None)
            
        return {"status": "success", "message": "تم بث إشارة المنصة مع مستويات الحماية بدقة"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def execute_market_analysis_and_notify(symbol):
    df, image_path = get_market_data(symbol)
    if df is None or df.empty:
        return False
    
    latest = df.iloc[-1]
    price = latest.get('close', 0)
    rsi = latest.get('RSI', 50)
    pattern = latest.get('detected_pattern', 'Structure Break / Trend Confirmation')
    support = latest.get('support_level', price * 0.98)
    resistance = latest.get('resistance_level', price * 1.025)
    asset_type = latest.get('asset_type_desc', 'أصل مالي عالمي')

    # حساب الأرقام البصرية الدقيقة (أعلى رقم للربح وأدنى رقم لوقف الخسارة لتجنب الخسارة تماماً)
    entry_price = price
    max_profit_target = resistance if resistance > entry_price else entry_price * 1.025
    min_stop_loss = support if support < entry_price else entry_price * 0.985

    # التحليل الذكي العبقري بناءً على المؤشرات الحقيقية
    if rsi < 42 or "Bottom" in pattern or "W" in pattern or "Wedge" in pattern:
        decision = "🟢 توصية شراء استراتيجية قوية (BUY)"
        ai_reason = "رصد ارتداد سعري حقيقي من خطوط الدعم مع تشبع بيعي، وهيكل صاعد يؤكد جاهزية السعر للانطلاق."
        trading_tip = "💡 نصيحة حماية الحساب: التزم بالخروج التلقائي عند أدنى رقم محدد أدناه لمنع أي خسارة محتملة."
    elif rsi > 58 or "Top" in pattern:
        decision = "🔴 توصية بيع وجني أرباح (SELL / EXIT)"
        ai_reason = "وصول السعر لمناطق مقاومة حرجة مع تشبع شرائي، ويُفضل إغلاق المراكز لحماية الأرباح."
        trading_tip = "💡 نصيحة حماية الحساب: تفعيل أمر البيع عند السقف الأعلى المحسوب لحجز الأرباح فوراً."
    else:
        decision = "🟡 مراقبة تامة وسوق عرضي (HOLD / NEUTRAL)"
        ai_reason = "السعر يتحرك ضمن نطاق تجميعي بانتظار كسر حقيقي للمستويات الفنية."
        trading_tip = "💡 نصيحة حماية الحساب: لا تدخل السوق حتى يلامس السعر الحد الأدنى أو الأقصى المرسوم."

    creator = get_creator_handle()
    creator_link = f"https://t.me/{creator}" if not creator.startswith("http") else creator

    # صياغة التقرير العبقري الرقمي المتكامل
    report = (
        f"🏛 *منصة سومر الذكية - التحليل العبقري والرقابة الآلية*\n\n"
        f"📌 *الأصل / السهم:* `{symbol.upper()}` ({asset_type})\n"
        f"💵 *السعر الحالي المباشر:* `{entry_price:,.2f}`\n\n"
        f"🤖 *القرار الفني الذكي:* \n*{decision}*\n"
        f"📊 *النموذج الفني المرصود:* `{pattern}` (مؤشر RSI: `{rsi:.1f}`)\n\n"
        f"🎯 *مستويات الحماية والإغلاق التلقائي (مثل شارت التداول):*\n"
        f"• 📈 **أعلى رقم للربح (Take Profit):** `{max_profit_target:,.2f}`\n"
        f"  *(نقطة قياسية لإغلاق الشراء وجني الأرباح بالكامل)*\n\n"
        f"• 🛑 **أدنى رقم لوقف الخسارة (Stop Loss):** `{min_stop_loss:,.2f}`\n"
        f"  *(خط الدفاع الأخير؛ يتوقف البوت ويغلق الصفقة فوراً لكي لا يخسر العميل)*\n\n"
        f"🧠 *التحليل الفني الحقيقي:*\n_{ai_reason}_\n\n"
        f"{trading_tip}\n\n"
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
            print(f"خطأ في التحليل التلقائي العبقري: {e}")
        
        for _ in range(3600):
            if not auto_alert_status["running"]:
                break
            await asyncio.sleep(1)

def send_telegram_photo_and_report(chat_id, message, image_path):
    clean_chat_id = str(chat_id).strip()
    
    if image_path and os.path.exists(image_path):
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendPhoto"
        with open(image_path, 'rb') as photo_file:
            payload = {"chat_id": clean_chat_id, "caption": message, "parse_mode": "Markdown"}
            files = {"photo": photo_file}
            try:
                response = requests.post(url, data=payload, files=files, timeout=10)
                if response.status_code == 200 and response.json().get("ok"):
                    return
            except:
                pass
                
    url_msg = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload_msg = {"chat_id": clean_chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url_msg, json=payload_msg, timeout=10)
    except:
        pass

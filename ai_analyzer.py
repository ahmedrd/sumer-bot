import os
from openai import OpenAI
import config

# تهيئة عميل الذكاء الاصطناعي (يمكنك وضع مفتاحك هنا أو عبر متغيرات البيئة)
# client = OpenAI(api_key="ضع_مفتاح_الذكاء_الاصطناعي_هنا")

def get_ai_market_analysis(df, symbol):
    """إرسال بيانات السوق الحالية إلى الذكاء الاصطناعي لاستخراج تحليل احترافي"""
    latest = df.iloc[-1]
    
    # تجهيز ملخص الأرقام لآخر شمعة
    market_data = (
        f"الأصل: {symbol}\n"
        f"سعر الاغلاق: {latest['close']}\n"
        f"أعلى سعر: {latest['high']}\n"
        f"أقل سعر: {latest['low']}\n"
        f"مؤشر القوة النسبية RSI: {latest['RSI']:.2f}\n"
        f"متوسط الحركة SMA 50: {latest.get('SMA_50', 0):.2f}\n"
    )

    prompt = f"""
    أنت محلل مالى وخبراء تداول محترف. هذه هي البيانات الفنية الحديثة لسوق {symbol}:
    {market_data}
    
    بناءً على هذه المعطيات، قم بتحليل السوق بدقة وأعطني الرد باللغة العربية حصراً وبالتنسيق التالي بالضبط:
    1. القرار النهائي (اختر واحداً فقط من: شراء (BUY)، بيع (SELL)، تريث (HOLD))
    2. السبب الفني للقرار باختصار شديد.
    """

    try:
        # ملاحظة: يمكنك تفعيل هذا الاتصال عند وضع مفتاح الـ API الخاص بك
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0.3
        # )
        # return response.choices[0].message.content
        
        # محاكاة الاستجابة الذكية ريثما تربط المفتاح:
        return f"🎯 القرار النهائي: تريث (HOLD)\n\n💡 التحليل الآلي: بناءً على معطيات السعر ومؤشر RSI ({latest['RSI']:.2f})، السوق يعاني من تذبذب عرضي، ويفضل الانتظار حتى كسر المقاومة."
        
    except Exception as e:
        return f"❌ حدث خطأ أثناء تحليل الذكاء الاصطناعي: {e}"
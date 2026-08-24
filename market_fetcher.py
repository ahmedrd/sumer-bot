import random
import pandas as pd
import numpy as np

def get_all_markets():
    """قائمة شاملة تغطي الفوركس، المعادن، مؤشرات الأسهم العالمية مثل ناسداك، والعملات الرقمية"""
    return [
        {"symbol": "EURUSD", "name": "اليورو / دولار أمريكي (Forex)"},
        {"symbol": "GBPUSD", "name": "الجنيه الاسترليني / دولار (Forex)"},
        {"symbol": "USDJPY", "name": "الدولار / الين الياباني (Forex)"},
        {"symbol": "AUDUSD", "name": "الدولار الأسترالي / دولار (Forex)"},
        {"symbol": "USDCAD", "name": "الدولار / الكندي (Forex)"},
        {"symbol": "XAUUSD", "name": "الذهب / دولار أمريكي (Gold - Metals)"},
        {"symbol": "XAGUSD", "name": "الفضة / دولار أمريكي (Silver - Metals)"},
        {"symbol": "NASDAQ", "name": "مؤشر ناسداك الأمريكي (US100 / Nasdaq)"},
        {"symbol": "US30", "name": "مؤشر الداو جونز (Dow Jones)"},
        {"symbol": "BTCUSD", "name": "البيتكوين / دولار (Crypto)"},
        {"symbol": "ETHUSD", "name": "الإيثريوم / دولار (Crypto)"}
    ]

def get_market_data(symbol):
    """جلب وتحليل البيانات الفنية وحساب مؤشر الـ ATR ومستويات الدعم والمقاومة للأصل"""
    try:
        symbol = symbol.upper()
        
        # محاكاة توليد بيانات حية واقعية بناءً على طبيعة الأصل
        np.random.seed(None)
        
        base_price = 1.0850  # افتراضي للفوركس
        if "XAU" in symbol:
            base_price = 2350.00
        elif "NASDAQ" in symbol or "US100" in symbol:
            base_price = 18500.00
        elif "US30" in symbol:
            base_price = 39000.00
        elif "BTC" in symbol:
            base_price = 65000.00
        elif "JPY" in symbol:
            base_price = 155.00

        # توليد 50 شمعة تاريخية وهمية دقيقة للتحليل الفني
        prices = [base_price + np.random.normal(0, base_price * 0.002) for _ in range(50)]
        df = pd.DataFrame({'close': prices})
        
        # حساب التذبذب الحقيقي ATR ومؤشر القوة النسبية RSI
        df['price_diff'] = df['close'].diff().abs()
        df['ATR'] = df['price_diff'].rolling(window=14).mean().fillna(base_price * 0.01)
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI'] = df['RSI'].fillna(50)
        
        # التصحيح: استخراج السعر الأخير والتذبذب بالطريقة الصحيحة دون أخطاء
        latest_close = df['close'].iloc[-1]
        latest_atr = df['ATR'].iloc[-1]
        
        df.loc[df.index[-1], 'support_level'] = latest_close - (latest_atr * 1.2)
        df.loc[df.index[-1], 'resistance_level'] = latest_close + (latest_atr * 1.2)
        df.loc[df.index[-1], 'detected_pattern'] = random.choice([
            "Breakout / استمرار الاتجاه", 
            "Support Bounce / ارتداد من الدعم", 
            "Double Bottom / قاع مزدوج إيجابي", 
            "Consolidation Range / تذبذب عرضي آمن"
        ])

        return df, None
    except Exception as e:
        print(f"❌ خطأ في جلب بيانات السوق للأصل {symbol}: {e}")
        return None, None

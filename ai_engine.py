def make_trading_decision(df):
    """تحليل قراءات السوق واستخراج قرار منطقي (شراء، بيع، تريث)"""
    latest = df.iloc[-1]
    
    rsi = latest['RSI']
    close_price = latest['close']
    sma_50 = latest['SMA_50']
    
    decision = "تريث (HOLD)"
    reason = "السوق في حالة استقرار نسبي ولا توجد إشارات قوية واضحة."
    
    # استراتيجية تحليل ذكية مبنية على المؤشرات الفنية
    if rsi < 30 and close_price > sma_50:
        decision = "شراء (BUY)"
        reason = f"مؤشر القوة النسبية RSI منخفض للغاية ({rsi:.2f}) ويشير إلى تشبع البيع (فرصة ارتداد)، والسعر أعلى من متوسط 50."
    elif rsi > 70:
        decision = "بيع (SELL)"
        reason = f"مؤشر القوة النسبية RSI مرتفع للغاية ({rsi:.2f}) ويشير إلى تشبع الشراء (احتمال هبوط تصحيحي)."
        
    return {
        "decision": decision,
        "price": close_price,
        "rsi": rsi,
        "reason": reason
    }
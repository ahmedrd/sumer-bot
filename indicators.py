import pandas_ta as ta

def calculate_indicators(df):
    """حساب مؤشر القوة النسبية RSI والمتوسطات المتحركة بدقة عالية"""
    # حساب مؤشر RSI بفترة 14 شمعة
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    # حساب المتوسطات المتحركة البسيطة
    df['SMA_50'] = ta.sma(df['close'], length=50)
    df['SMA_200'] = ta.sma(df['close'], length=200)
    
    return df
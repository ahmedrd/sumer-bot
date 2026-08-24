import pandas as pd
from binance.client import Client

def get_binance_data(symbol="BTCUSDT", interval="1h", limit=100):
    """جلب البيانات التاريخية واللحظية من منصة Binance مجاناً وبدون مفاتيح API خاصة بالمنصة"""
    try:
        client = Client()
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
    except Exception as e:
        print(f"❌ خطأ أثناء جلب البيانات من بينانس: {e}")
        return None
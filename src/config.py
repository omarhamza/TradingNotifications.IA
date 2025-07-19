# Configuration
TELEGRAM_TOKEN = "7706670085:AAGRMve7EuhFo1i8C2U22JdNPyGyvjN4-N8"
TELEGRAM_CHAT_ID = "7664939619"

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

TIMEFRAME = '1h'
MAX_DAYS=365

features = [
    'rsi', 'rsi_delta', 'macd', 'macd_signal',
    'ema_20', 'ema_50', 'bb_high', 'bb_low',
    'obv', 'volatility', 'stoch_k', 'stoch_d'
]
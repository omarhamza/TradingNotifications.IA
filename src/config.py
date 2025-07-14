# Configuration
TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

SLEEP_TIME = 15
TIMEFRAME = '1h'
MAX_DAYS=365

features = [
    'rsi', 'rsi_delta', 'macd', 'macd_signal',
    'ema_20', 'ema_50', 'bb_high', 'bb_low',
    'obv', 'volatility', 'stoch_k', 'stoch_d'
]
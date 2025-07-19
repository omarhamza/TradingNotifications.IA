import time
import os
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""
SLEEP_TIME = 15
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
TIMEFRAME = '1h'
MAX_DAYS=365

features = [
    'rsi', 'rsi_delta', 'macd', 'macd_signal',
    'ema_20', 'ema_50', 'bb_high', 'bb_low',
    'obv', 'volatility', 'stoch_k', 'stoch_d'
]

# ---------------------- Envoyer message via télégram ---------------------- #
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Erreur envoi Telegram :", e)
        
send_telegram_message(f"✅ *Start running !*")

# ---- 1. Charger les données depuis Binance ----
def fetch_crypto_data_incremental(symbol, max_days):
    CSV_FILE = f"historical_{symbol.replace('/', '')}_{TIMEFRAME}.csv"
    exchange = ccxt.binance()
    limit = 1000
    all_data = []

    if os.path.exists(CSV_FILE):
        # Charger les données existantes
        df_existing = pd.read_csv(CSV_FILE, parse_dates=['timestamp'])
        df_existing.set_index('timestamp', inplace=True)
        last_timestamp = df_existing.index[-1]
        since = int(last_timestamp.timestamp() * 1000) + 1  # En ms
    else:
        # Pas de fichier : démarrer depuis now - MAX_DAYS
        since = exchange.parse8601((pd.Timestamp.utcnow() - pd.Timedelta(days=MAX_DAYS)).isoformat())
        df_existing = pd.DataFrame()

    while True:
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, since=since, limit=limit)
            if not data:
                break
            all_data += data
            since = data[-1][0] + 1
            if len(data) < limit:
                break
            time.sleep(0.2)
        except Exception as e:
            print(f"Erreur récupération : {e}")
            break

    if not all_data:
        print(f"Aucune nouvelle donnée pour {symbol}")
        return df_existing

    df_new = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_new['timestamp'] = pd.to_datetime(df_new['timestamp'], unit='ms')
    df_new.set_index('timestamp', inplace=True)

    # Fusionner sans doublon
    df = pd.concat([df_existing, df_new])
    df = df[~df.index.duplicated(keep='last')]
    df.sort_index(inplace=True)

    # Sauvegarde mise à jour
    df.to_csv(CSV_FILE)
    print(f"✅ Données mises à jour pour {symbol}")

    return df

# ---- 2. Ajouter des indicateurs techniques ----
def enrich_features(df):
    df['rsi'] = RSIIndicator(close=df['close']).rsi()
    df['macd'] = MACD(close=df['close']).macd()
    df['macd_signal'] = MACD(close=df['close']).macd_signal()
    df['ema_20'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
    df['ema_50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()

    bb = BollingerBands(close=df['close'])
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['obv'] = OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume()

    # Stochastic Oscillator
    stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()

    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(10).std()
    df['rsi_delta'] = df['rsi'].diff()
    df.dropna(inplace=True)
    return df

# ---- 3. Entraînement du modèle ML ----
def train_model_from_csv(csv_file):
    df = pd.read_csv(csv_file, parse_dates=['timestamp'])
    df.set_index('timestamp', inplace=True)
    df['future_return'] = df['close'].shift(-3) / df['close'] - 1
    df['target'] = (df['future_return'] > 0.01).astype(int)
    df.dropna(subset=features + ['target'], inplace=True)

    X = df[features]
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)

    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("📊 Rapport de performance :")
    print(classification_report(y_test, y_pred))

    return model, df

# ---- 4. Envoi d’un message Telegram ----
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Erreur envoi Telegram :", e)

# ---- 5. Logique principale ----
def ShouldIBuyCrypto():
    for symbol in SYMBOLS:
        try:
            df = fetch_crypto_data_incremental(symbol, max_days=MAX_DAYS)
            df = enrich_features(df)
            df['symbol'] = symbol

            # 🔁 Enregistre le DataFrame enrichi dans le CSV mis à jour
            CSV_FILE = f"historical_{symbol.replace('/', '')}_{TIMEFRAME}.csv"
            df.to_csv(CSV_FILE)
        except Exception as e:
            print(f"Erreur chargement pour {symbol} : {e}")

    print("\n📈 Signaux de trading actuels :\n")

    for symbol in SYMBOLS:
        CSV_FILE = f"historical_{symbol.replace('/', '')}_{TIMEFRAME}.csv"
        try:
            model, df_symbol = train_model_from_csv(CSV_FILE)
            last_features = df_symbol[features].iloc[-1].values.reshape(1, -1)
            prediction = model.predict(last_features)[0]
            latest_rsi = df_symbol['rsi'].iloc[-1]

            if prediction == 1:
                send_telegram_message(f"🚀 *Signal d'achat détecté !*\n"
                                      f"Il est peut-être temps d'acheter *{symbol}* !\n"
                                      f"RSI : {latest_rsi:.2f}")
            else:
                print(f"😐 Aucun signal d'achat pour {symbol}.")
        except Exception as e:
            print(f"Erreur de prédiction pour {symbol} : {e}")

try:
    ShouldIBuyCrypto()
except Exception as e:
    notify(f"❌❌❌ Erreur globale : {e}")
import ccxt
import pandas as pd
import numpy as np
import requests
import time
from ta.momentum import RSIIndicator
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
RSI_THRESHOLD_SELL = 70
combined_df = []
TIMEFRAME = '1h'
DAYS_BACK = 180

features = [
    'rsi', 'rsi_delta', 'macd', 'macd_signal',
    'ema_20', 'ema_50', 'bb_high', 'bb_low',
    'obv', 'volatility'
]

# ---- 1. Charger les données depuis Binance ----
def fetch_crypto_data(symbol, max_days=180):
    exchange = ccxt.binance()
    since = exchange.parse8601((pd.Timestamp.utcnow() - pd.Timedelta(days=max_days)).isoformat())
    all_data = []
    limit = 1000

    while True:
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, since=since, limit=limit)
            if not data:
                break

            all_data += data
            since = data[-1][0] + 1  # passer à la bougie suivante

            if len(data) < limit:
                break  # pas plus de données à récupérer

        except Exception as e:
            print(f"Erreur récupération : {e}")
            break

        time.sleep(0.2)  # pour éviter d’être bloqué par l’API

    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
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
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(10).std()
    df['rsi_delta'] = df['rsi'].diff()

    df.dropna(inplace=True)
    return df

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

# Should I buy crypto
def ShouldIByCrypto():
    for symbol in SYMBOLS:
        try:
            df = fetch_crypto_data(symbol)
            df = enrich_features(df)
            df['symbol'] = symbol
            combined_df.append(df)
        except Exception as e:
            print(f"Erreur chargement pour {symbol} : {e}")

    # ----- 2. Combiner les données -----
    if not combined_df:
        print("❌ Aucune donnée disponible pour l'entraînement.")
        return

    df_all = pd.concat(combined_df)
    df_all.reset_index(inplace=True)

    # ----- 3. Calcul des targets -----
    df_all['future_return'] = df_all.groupby('symbol')['close'].shift(-3) / df_all['close'] - 1
    df_all['target'] = (df_all['future_return'] > 0.01).astype(int)

    df_all.dropna(subset=features + ['target'], inplace=True)
    X = df_all[features]
    y = df_all['target']

    # ----- 4. Entraînement modèle ML -----
    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("🔍 Rapport de performance du modèle :\n")
    print(classification_report(y_test, y_pred))

    # ----- 5. Prédiction finale sur chaque symbole -----
    print("\n📈 Signaux de trading actuels :\n")
    for symbol in SYMBOLS:
        df_symbol = df_all[df_all['symbol'] == symbol]
        if df_symbol.empty:
            continue

        try:
            last_features = df_symbol[features].iloc[-1].values.reshape(1, -1)
            prediction = model.predict(last_features)[0]
            latest_rsi = df_symbol['rsi'].iloc[-1]

            if prediction == 1:
                send_telegram_message(f"🚀 *Signal d'achat détecté !* \n"
                                      f"Il est peut-être temps d'acheter *{symbol}* ! \n"
                                      f"RSI: {latest_rsi:.2f}")
            else:
                print(f"😐 Aucun signal d'achat pour {symbol} à cette heure.")

        except Exception as e:
            print(f"Erreur de prédiction pour {symbol} : {e}")


# 🔁 Boucle de surveillance
while True:
    try:
        ShouldIByCrypto()

    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"⏳ Waiting {SLEEP_TIME} minutes for next run...\n")
    time.sleep(SLEEP_TIME * 60)
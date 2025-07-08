import ccxt
import pandas as pd
import numpy as np
import requests
import time
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

TELEGRAM_TOKEN = "7706670085:AAGRMve7EuhFo1i8C2U22JdNPyGyvjN4-N8"
TELEGRAM_CHAT_ID = "7664939619"
SLEEP_TIME = 15

# ⚙️ Liste des cryptos à surveiller
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
RSI_THRESHOLD_SELL = 70
combined_df = []

# ---- 1. Charger les données depuis Binance ----
def fetch_crypto_data(symbol, timeframe='1h', limit=500):
    exchange = ccxt.binance()
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
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

            df_all = pd.concat(combined_df)
            df_all.reset_index(inplace=True)
             
            # 3. Label (1 = Buy, 0 = Hold)
            df_all['future_return'] = df_all.groupby('symbol')['close'].shift(-3) / df_all['close'] - 1
            df_all['target'] = (df_all['future_return'] > 0.01).astype(int)

            features = [
                'rsi', 'rsi_delta', 'macd', 'macd_signal',
                'ema_20', 'ema_50', 'bb_high', 'bb_low',
                'obv', 'volatility'
            ]

            # ---- 4. Label : achat si prix augmente >1% dans 3 heures ----
            df_all.dropna(subset=features + ['target'], inplace=True)
            X = df_all[features]
            y = df_all['target']
        
            # 5 Entraînement du modèle ML
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
        
            # 6. Évaluation
            y_pred = model.predict(X_test)
            print(classification_report(y_test, y_pred))
        
            # 7. Prédiction sur le dernier point
            last_features = X.iloc[[-1]]
            prediction = model.predict(last_features)[0]

            # 8. Send message
            if prediction == 1:
                send_telegram_message(f"🚀 *Signal d'achat détecté !* Il est peut-être temps d'acheter *{symbol}* !")
            else:
                print(f"😐 Aucun signal d'achat pour {symbol} à cette heure.")
            
            print("Message envoyé sur Telegram.")
        except Exception as e:
            print(f"Erreur pour {symbol} : {e}")


# 🔁 Boucle de surveillance
while True:
    try:
        ShouldIByCrypto()

    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"⏳ Waiting {SLEEP_TIME} minutes for next run...\n")
    time.sleep(SLEEP_TIME * 60)
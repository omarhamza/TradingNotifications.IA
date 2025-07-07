import ccxt
import pandas as pd
import numpy as np
import requests
from ta.momentum import RSIIndicator
from ta.trend import MACD
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os


TELEGRAM_TOKEN = ""
TELEGRAM_CHAT_ID = ""

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

# ⚙️ Liste des cryptos à surveiller
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

# ⚙️ Seuils d’achat fictifs (exemple)
BUY_THRESHOLDS = {
    'BTC/USDT': 58000,
    'ETH/USDT': 3100,
    'SOL/USDT': 120
}

# Should I buy crypto
def ShouldIByCrypto():
    for symbol in SYMBOLS:
        try:
            # 1. Charger les données de Binance (1h)
            exchange = ccxt.binance()
            data = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=500)
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 2. Indicateurs techniques
            df['rsi'] = RSIIndicator(close=df['close']).rsi()
            macd = MACD(close=df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            
            # 3. Label (1 = Buy, 0 = Hold)
            future_return = df['close'].shift(-3) / df['close'] - 1
            df['target'] = np.where(future_return > 0.01, 1, 0)  # achat si +1% dans 3h
            
            # 4. Entraînement du modèle
            df.dropna(inplace=True)
            X = df[['rsi', 'macd', 'macd_signal']]
            y = df['target']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            model = RandomForestClassifier(n_estimators=100)
            model.fit(X_train, y_train)
            
            # 5. Évaluation
            y_pred = model.predict(X_test)
            print(classification_report(y_test, y_pred))
            
            # 6. Prédiction sur le dernier point
            prediction = model.predict([X.iloc[-1]])[0]

            # 7. Send message
            if prediction == 1:
                send_telegram_message(f"🚀 *Signal d'achat détecté !* Il est peut-être temps d'acheter *{symbol}* !")
            elif prediction == 0:
                send_telegram_message(f"😐 Aucun signal d'achat pour {symbol} à cette heure.")
            else:
                send_telegram_message(f"📉 *Signal de vente détecté !* Il est peut-être temps d'acheter *{symbol}* !")
            
            print("Message envoyé sur Telegram.")
        except Exception as e:
            print(f"Erreur pour {symbol} : {e}")


# 🔁 Boucle de surveillance
#while True:
ShouldIByCrypto()
time.sleep(60)  # attends 60 sec avant de recommencer

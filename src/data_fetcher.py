import ccxt
import os
import pandas as pd
import time
from config import TIMEFRAME, MAX_DAYS

def fetch_crypto_data_incremental(symbol):
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
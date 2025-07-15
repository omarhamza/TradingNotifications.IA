import ccxt
import os
import pandas as pd
import time
from config import TIMEFRAME, MAX_DAYS
from delete_csv_files import delete_csv_files

def fetch_crypto_data_incremental(symbol):
    CSV_FILE = f"historical_{symbol.replace('/', '')}_{TIMEFRAME}.csv"
    exchange = ccxt.binance()
    limit = 1000
    all_data = []
    since = exchange.parse8601((pd.Timestamp.utcnow() - pd.Timedelta(days=MAX_DAYS)).isoformat())

    if os.path.exists(CSV_FILE):
        delete_csv_files()

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

    df_new = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_new['timestamp'] = pd.to_datetime(df_new['timestamp'], unit='ms')
    df_new.set_index('timestamp', inplace=True)

    # Fusionner sans doublon
    df = pd.DataFrame(df_new)
    df = df[~df.index.duplicated(keep='last')]
    df.sort_index(inplace=True)

    # Sauvegarde mise à jour
    df.to_csv(CSV_FILE)
    print(f"✅ Données mises à jour pour {symbol}")

    return df
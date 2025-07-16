from config import SYMBOLS, TIMEFRAME, features
from send_telegram_message import notify
from data_fetcher import fetch_crypto_data_incremental
from add_indicators import enrich_features
from train_model import train_model_from_csv

def ShouldIBuyCrypto():
    for symbol in SYMBOLS:
        try:
            df = fetch_crypto_data_incremental(symbol)
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
                notify(f"🚀 *Signal d'achat détecté !*\n"
                                      f"Il est peut-être temps d'acheter *{symbol}* !\n"
                                      f"RSI : {latest_rsi:.2f}")
            else:
                print(f"😐 Aucun signal d'achat pour {symbol}.")
        except Exception as e:
            print(f"Erreur de prédiction pour {symbol} : {e}")
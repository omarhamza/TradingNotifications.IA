import time
from config import SLEEP_TIME
from send_telegram_message import notify
from decision import ShouldIBuyCrypto
        
notify(f"✅ *Start running XGB V1.0!*")

while True:
    try:
        ShouldIBuyCrypto()
    except Exception as e:
        notify(f"❌❌❌ Erreur globale : {e}")
    print(f"⏳ Pause de {SLEEP_TIME} minutes avant le prochain cycle...\n")
    time.sleep(SLEEP_TIME * 60)

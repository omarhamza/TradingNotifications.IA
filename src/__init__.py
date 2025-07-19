import time
from send_telegram_message import notify
from decision import ShouldIBuyCrypto
        
notify(f"✅ *Start running XGB V1.0!*")

try:
    ShouldIBuyCrypto()
except Exception as e:
    notify(f"❌❌❌ Erreur globale : {e}")
print(f"⏳ Pause de {SLEEP_TIME} minutes avant le prochain cycle...\n")
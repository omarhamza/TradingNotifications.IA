from send_telegram_message import notify
from decision import ShouldIBuyCrypto

try:
    ShouldIBuyCrypto()
except Exception as e:
    notify(f"❌❌❌ Erreur globale : {e}")
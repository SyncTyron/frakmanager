### logs.py
import logging
from datetime import datetime
import os
# Stelle sicher, dass der Log-Ordner existiert, bevor das Logging initialisiert wird
os.makedirs("logs", exist_ok=True)

logging.basicConfig(filename="logs/bot.log", level=logging.DEBUG)

def debug(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    logging.debug(log_msg)
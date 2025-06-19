### logs.py
import logging
from datetime import datetime

logging.basicConfig(filename='logs/bot.log', level=logging.DEBUG)

def debug(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    logging.debug(log_msg)
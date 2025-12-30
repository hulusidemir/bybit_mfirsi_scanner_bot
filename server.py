import threading
import time
import os
from flask import Flask
from src.main import job
from src.telegram_sender import TelegramSender

app = Flask(__name__)

# Global variable to control the loop
running = True

def run_bot():
    print("Bot thread started...")
    sender = TelegramSender()
    startup_msg = "🚀 rsi_mfi_scanner Bot Started Scanning (Server Mode)"
    try:
        sender.send_message(startup_msg)
    except Exception as e:
        print(f"Failed to send startup message: {e}")
    
    sent_alerts = {}
    
    while running:
        try:
            print("Running scan job...")
            job(sent_alerts)
            print("Scan job finished. Waiting 5 minutes...")
            time.sleep(300) # 5 minutes sleep
        except Exception as e:
            print(f"Error in bot loop: {e}")
            time.sleep(60) # Wait 1 minute on error before retrying

@app.route('/')
def health_check():
    return "Bot is running!", 200

def start_bot_thread():
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    start_bot_thread()
    # Get port from environment variable for Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
else:
    # Start thread when imported by Gunicorn
    start_bot_thread()

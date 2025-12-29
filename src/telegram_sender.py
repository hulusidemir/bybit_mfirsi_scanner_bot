import asyncio
from telegram import Bot
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class TelegramSender:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.bot = Bot(token=self.token)

    async def send_message_async(self, message):
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
        except Exception as e:
            print(f"Error sending telegram message: {e}")

    def send_message(self, message):
        """Synchronous wrapper for sending message"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we are already in an event loop (e.g. jupyter or async app)
                loop.create_task(self.send_message_async(message))
            else:
                asyncio.run(self.send_message_async(message))
        except RuntimeError:
            # Fallback for when no event loop is present
            asyncio.run(self.send_message_async(message))

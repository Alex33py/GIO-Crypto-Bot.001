# bot/telegram_sender.py

import requests
import json
import logging

logger = logging.getLogger(__name__)


class TelegramSender:
    """Send alerts to Telegram"""

    def __init__(self, config_file='config/telegram_config.json'):
        with open(config_file) as f:
            cfg = json.load(f)

        self.token = cfg['bot_token']
        self.chat_id = cfg['chat_id']
        self.enabled = cfg['enabled']
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_signal(self, signal):
        """Send signal alert"""

        if not self.enabled:
            return

        message = f"""
🚨 НОВЫЙ СИГНАЛ!

Сценарий: {signal['scenario']}
⏰ {signal['timestamp']}

📊 Entry: ${signal['entry']:,.2f}
🛑 SL: ${signal['sl_price']:,.2f}
💰 TP: ${signal['tp']:,.2f}

📈 ADX: {signal['adx']:.1f}
📊 RSI: {signal['rsi']:.1f}
⏱️ ATR: {signal['atr']:.1f}
"""

        try:
            requests.post(
                f"{self.base_url}/sendMessage",
                data={'chat_id': self.chat_id, 'text': message}
            )
            logger.info("✅ Telegram alert sent")
        except Exception as e:
            logger.error(f"❌ Telegram error: {e}")

    def send_test(self):
        """Send test message"""

        message = "✅ GIO.BOT Telegram connection test - OK!"

        try:
            requests.post(
                f"{self.base_url}/sendMessage",
                data={'chat_id': self.chat_id, 'text': message}
            )
            logger.info("✅ Test message sent")
            return True
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False


# TEST
if __name__ == "__main__":
    sender = TelegramSender()
    sender.send_test()

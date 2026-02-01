"""
Telegram Bot Notifier for sending prep packs to bankers' phones
"""
import asyncio
import logging
from config import Config
from telegram_bot import send_telegram_notification

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Sends prep pack summaries to bankers via Telegram"""
    
    def __init__(self):
        self.bot_token = getattr(Config, 'TELEGRAM_BOT_TOKEN', None)
        self.chat_id = getattr(Config, 'TELEGRAM_CHAT_ID', None)
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram notifications disabled - missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
    
    def send_prep_pack(self, client_name: str, report_markdown: str):
        """Send prep pack notification"""
        if not self.enabled:
            return
        
        try:
            # Format message for Telegram (max 4096 chars)
            header = f"📊 *Prep Pack Generated*\n\n"
            header += f"*Client:* {client_name}\n"
            header += f"━━━━━━━━━━━━━━━━━━━━\n\n"
            
            # Truncate markdown if too long
            max_content = 4096 - len(header) - 100
            content = report_markdown[:max_content]
            if len(report_markdown) > max_content:
                content += "\n\n_[Report truncated - view full version in web app]_"
            
            message = header + content
            
            # Send message using the bot module
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                send_telegram_notification(self.bot_token, self.chat_id, message)
            )
            loop.close()
            
            logger.info(f"Telegram notification sent for client: {client_name}")
            
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}", exc_info=True)

# Singleton instance
telegram_notifier = TelegramNotifier()

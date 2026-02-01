"""
Run DONNA Telegram Bot
This starts the bidirectional Telegram bot that can receive commands and send notifications
"""
import logging
import os
from dotenv import load_dotenv
from telegram_bot import DONNATelegramBot

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the bot"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:5000")
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        logger.error("Please add TELEGRAM_BOT_TOKEN to your .env file")
        return
    
    logger.info("Starting DONNA Telegram Bot...")
    logger.info(f"API Base URL: {api_base_url}")
    
    bot = DONNATelegramBot(bot_token, api_base_url)
    bot.run_sync()  # Use synchronous runner

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

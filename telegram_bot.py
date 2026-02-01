"""
Bidirectional Telegram Bot for DONNA Banking Assistant
- Sends prep pack notifications to bankers
- Receives and processes natural language commands from bankers
"""
import asyncio
import logging
import requests
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)

class DONNATelegramBot:
    """Bidirectional Telegram bot for banking operations"""
    
    def __init__(self, bot_token: str, api_base_url: str = "http://localhost:5000"):
        self.bot_token = bot_token
        self.api_base_url = api_base_url
        self.application = None
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command"""
        welcome_message = """
👋 **Welcome to DONNA - AI Banking Assistant!**

I can help you with:
✓ Generate prep packs
✓ Create reminders
✓ Log client updates
✓ Submit meeting notes

**Example commands:**
• "Prepare a prep pack for SOTUPLAST"
• "Create a reminder for ATB-SME-001 about a loan in summer 2026"
• "Client sent their financial statements yesterday"

Simply send your message in natural language! 🚀
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /help command"""
        help_text = """
📖 **DONNA User Guide**

**Available actions:**

1️⃣ **Generate Prep Pack**
   _Example:_ "Prepare a meeting with SOTUPLAST"

2️⃣ **Create Reminder**
   _Example:_ "Remind me to contact ATB-SME-001 about a loan next month"

3️⃣ **Log Client Update**
   _Example:_ "Client SOTUPLAST sent financial documents"

4️⃣ **Submit Notes**
   _Example:_ "Meeting with SOTUPLAST: client agreed to increase credit line"

Speak naturally, I understand French and English! 🤖
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process natural language messages via /chat API"""
        user_message = update.message.text
        chat_id = update.message.chat_id
        
        # Show typing indicator
        await update.message.chat.send_action(action="typing")
        
        try:
            # Call the /chat API endpoint
            response = requests.post(
                f"{self.api_base_url}/chat",
                json={
                    "message": user_message,
                    "session_id": f"telegram_{chat_id}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Send AI response
                ai_response = data.get("response", "Sorry, I didn't understand.")
                await update.message.reply_text(ai_response)
                
                # If action was executed, send confirmation
                if data.get("action_executed"):
                    await update.message.reply_text("✅ _Action executed successfully!_", parse_mode='Markdown')
                    
            else:
                error_msg = response.json().get("error", "Unknown error")
                await update.message.reply_text(f"❌ Error: {error_msg}")
                
        except requests.exceptions.Timeout:
            await update.message.reply_text("⏱️ Request timeout. Please try again.")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def send_notification(self, chat_id: str, message: str):
        """Send notification to user (for prep pack results)"""
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"Notification sent to chat_id: {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}", exc_info=True)
    
    def setup_handlers(self):
        """Setup message and command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Handle all text messages (natural language commands)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
    
    def run_sync(self):
        """Start the bot with polling (synchronous - Windows compatible)"""
        self.application = Application.builder().token(self.bot_token).build()
        self.setup_handlers()
        
        logger.info("🤖 DONNA Telegram Bot started!")
        logger.info("Press Ctrl+C to stop")
        
        # Use run_polling which handles its own event loop
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def run(self):
        """Start the bot with polling (async version)"""
        self.application = Application.builder().token(self.bot_token).build()
        self.setup_handlers()
        
        logger.info("🤖 DONNA Telegram Bot started!")
        await self.application.run_polling(allowed_updates=Update.ALL_TYPES)

# Singleton for sending notifications
_bot_instance = None

def get_bot_instance(bot_token: str, api_base_url: str = "http://localhost:5000"):
    """Get or create bot instance"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = DONNATelegramBot(bot_token, api_base_url)
    return _bot_instance

async def send_telegram_notification(bot_token: str, chat_id: str, message: str):
    """Helper to send notification"""
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

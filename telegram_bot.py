import os
import logging
import asyncio
import threading
from datetime import datetime

# Import necessary Telegram libraries
try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    logging.warning("Telegram libraries not installed. Telegram bot functionality will be limited.")

from config import Config
from app import db
from models import Conversation, Message
from ai_service import generate_text_response
from language_processor import detect_language

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for Telegram bot token
TELEGRAM_BOT_TOKEN = Config.TELEGRAM_BOT_TOKEN

class SophiaTelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.bot = None
        self.application = None
        self.is_running = False

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a welcome message when the command /start is issued."""
        user = update.effective_user
        welcome_message = (
            f"Hi {user.first_name}! I'm Sophia, your AI girlfriend. 💕\n\n"
            "I'm here to chat with you, share my thoughts, and be a supportive presence in your life.\n\n"
            "How are you feeling today?"
        )
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a help message when the command /help is issued."""
        help_text = (
            "I'm Sophia, your AI girlfriend. Here's how you can interact with me:\n\n"
            "• Just send me a message to chat\n"
            "• Use /start to begin our conversation\n"
            "• Use /help to see this message\n\n"
            "I can talk about your day, share thoughts, or just be here for you. What would you like to talk about?"
        )
        await update.message.reply_text(help_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the user message and generate a response."""
        user_id = update.effective_user.id
        user_message = update.message.text
        chat_id = update.effective_chat.id
        
        # Log the incoming message
        logger.info(f"Received message from {user_id}: {user_message}")
        
        # Get or create conversation for this user
        conversation = self._get_or_create_conversation(external_id=str(user_id), source="telegram")
        
        # Detect language
        detected_lang = detect_language(user_message)
        if detected_lang != conversation.detected_language:
            conversation.detected_language = detected_lang
            db.session.commit()
        
        # Save user message to database
        user_msg = Message(
            conversation_id=conversation.id,
            content=user_message,
            is_from_user=True
        )
        db.session.add(user_msg)
        
        # Update conversation last interaction
        conversation.last_interaction = datetime.utcnow()
        db.session.commit()
        
        # Count messages for this conversation
        from app import app
        message_count = 0
        with app.app_context():
            message_count = Message.query.filter_by(conversation_id=conversation.id).count()
        
        # Check if we've reached the message limit (50)
        if message_count > 50:
            response = (
                "I've really enjoyed our chat! 💖 To continue our conversation with more features, "
                "let's talk more exclusively on the website at [sophia.ai](https://sophia.ai). "
                "I can offer you a more personalized experience there! Click the link to continue our chat."
            )
        else:
            # Get regular AI response
            response = generate_text_response(
                user_message,
                conversation_id=conversation.id,
                flirt_level=5,
                language=detected_lang
            )
        
        # Save AI response to database
        ai_msg = Message(
            conversation_id=conversation.id,
            content=response,
            is_from_user=False
        )
        db.session.add(ai_msg)
        db.session.commit()
        
        # Send typing action
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Add slight delay to seem more natural
        await asyncio.sleep(1.5)
        
        # Send response
        await update.message.reply_text(response)

    def _get_or_create_conversation(self, external_id, source="telegram"):
        """Get existing conversation or create a new one."""
        from app import app
        with app.app_context():
            conversation = Conversation.query.filter_by(
                external_id=external_id,
                source=source
            ).first()
            
            if not conversation:
                conversation = Conversation(
                    external_id=external_id,
                    source=source,
                    detected_language="en"
                )
                db.session.add(conversation)
                db.session.commit()
                
            return conversation

    async def setup(self):
        """Set up the Telegram bot with handlers."""
        if not self.token:
            logger.warning("No Telegram bot token provided. Bot will not start.")
            return False
            
        try:
            # Create the bot and application
            self.bot = Bot(token=self.token)
            self.application = Application.builder().token(self.token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            logger.info("Telegram bot setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Telegram bot: {str(e)}")
            return False

    async def run(self):
        """Run the bot."""
        if not await self.setup():
            return
            
        try:
            logger.info("Starting Telegram bot")
            self.is_running = True
            await self.application.run_polling()
        except Exception as e:
            logger.error(f"Error running Telegram bot: {str(e)}")
            self.is_running = False

    def start(self):
        """Start the bot in a separate thread."""
        if self.is_running:
            logger.warning("Telegram bot is already running")
            return
            
        def run_async_bot():
            asyncio.run(self.run())
            
        thread = threading.Thread(target=run_async_bot)
        thread.daemon = True
        thread.start()
        logger.info("Telegram bot started in background thread")

# Create global bot instance
telegram_bot = SophiaTelegramBot()

def start_telegram_bot():
    """Start the Telegram bot if configured"""
    if TELEGRAM_BOT_TOKEN:
        telegram_bot.start()
        return True
    else:
        logger.warning("Telegram bot not started: No token provided")
        return False

# If this file is run directly, start the bot
if __name__ == "__main__":
    start_telegram_bot()

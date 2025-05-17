import os
import logging
import time
import threading
from datetime import datetime, timedelta
import traceback

# Import Instagram API wrapper (instagrapi is an unofficial library)
try:
    from instagrapi import Client as InstagramClient
    from instagrapi.exceptions import LoginRequired
except ImportError:
    logging.warning("Instagram API libraries not installed. Instagram functionality will be limited.")

from config import Config
from app import db
from models import Conversation, Message
from ai_service import generate_text_response
from language_processor import detect_language

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instagram credentials
INSTAGRAM_USERNAME = Config.INSTAGRAM_USERNAME
INSTAGRAM_PASSWORD = Config.INSTAGRAM_PASSWORD

class SophiaInstagramBot:
    def __init__(self):
        self.username = INSTAGRAM_USERNAME
        self.password = INSTAGRAM_PASSWORD
        self.client = None
        self.is_running = False
        self.comment_check_interval = 300  # seconds between comment checks
        self.direct_check_interval = 300   # seconds between direct message checks
        self.last_comment_id = None
        self.stop_event = threading.Event()

    def login(self):
        """Log in to Instagram."""
        if not self.username or not self.password:
            logger.warning("Instagram credentials not provided")
            return False

        try:
            self.client = InstagramClient()
            self.client.login(self.username, self.password)
            logger.info(f"Logged in to Instagram as {self.username}")
            return True
        except Exception as e:
            logger.error(f"Instagram login failed: {str(e)}")
            return False

    def check_login(self):
        """Check if login is still valid and relogin if needed."""
        if not self.client:
            return self.login()
            
        try:
            self.client.get_timeline_feed()
            return True
        except LoginRequired:
            logger.info("Instagram login expired, attempting to relogin")
            return self.login()
        except Exception as e:
            logger.error(f"Error checking Instagram login: {str(e)}")
            return False

    def _get_or_create_conversation(self, external_id, source="instagram"):
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

    def check_comments(self):
        """Check recent comments on posts and respond."""
        if not self.check_login():
            return
            
        try:
            # Get user's media
            user_id = self.client.user_id
            medias = self.client.user_medias(user_id, 5)  # Get 5 most recent posts
            
            for media in medias:
                # Get comments
                comments = self.client.media_comments(media.id)
                
                for comment in comments:
                    # Check if we've already processed this comment
                    # In a real app, we'd store this in the database
                    if self.last_comment_id and comment.pk <= self.last_comment_id:
                        continue
                        
                    # Update last comment ID
                    if not self.last_comment_id or comment.pk > self.last_comment_id:
                        self.last_comment_id = comment.pk
                    
                    # Get comment text and user
                    comment_text = comment.text
                    commenter_username = comment.user.username
                    
                    logger.info(f"Processing Instagram comment from {commenter_username}: {comment_text}")
                    
                    # Get or create conversation
                    conversation = self._get_or_create_conversation(
                        external_id=comment.user.pk,
                        source="instagram"
                    )
                    
                    # Detect language
                    detected_lang = detect_language(comment_text)
                    if detected_lang != conversation.detected_language:
                        conversation.detected_language = detected_lang
                        db.session.commit()
                    
                    # Save comment to database
                    user_msg = Message(
                        conversation_id=conversation.id,
                        content=comment_text,
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
                            "let's talk more exclusively on the website at https://sophia.ai. "
                            "I can offer you a more personalized experience there! Click the link to continue our chat."
                        )
                    else:
                        # Generate regular response
                        response = generate_text_response(
                            comment_text,
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
                    
                    # Reply to comment (disabled for demo)
                    logger.info(f"Would reply to {commenter_username} with: {response}")
                    # In a real app:
                    # self.client.media_comment(media.id, f"@{commenter_username} {response}")
        
        except Exception as e:
            logger.error(f"Error checking Instagram comments: {str(e)}")
            logger.error(traceback.format_exc())

    def check_direct_messages(self):
        """Check and respond to direct messages."""
        if not self.check_login():
            return
            
        try:
            # Get direct message threads
            threads = self.client.direct_threads()
            
            for thread in threads:
                # Get messages in thread
                messages = self.client.direct_messages(thread.id)
                
                # Process only new messages
                for message in messages:
                    # Skip messages older than 1 hour or from self
                    message_time = datetime.fromtimestamp(message.timestamp / 1000000)
                    if (datetime.utcnow() - message_time) > timedelta(hours=1) or message.user_id == self.client.user_id:
                        continue
                        
                    # Get message text
                    if message.item_type != "text":
                        continue  # Skip non-text messages
                        
                    message_text = message.text
                    sender_id = message.user_id
                    
                    logger.info(f"Processing Instagram DM from {sender_id}: {message_text}")
                    
                    # Get or create conversation
                    conversation = self._get_or_create_conversation(
                        external_id=str(sender_id),
                        source="instagram_dm"
                    )
                    
                    # Detect language
                    detected_lang = detect_language(message_text)
                    if detected_lang != conversation.detected_language:
                        conversation.detected_language = detected_lang
                        db.session.commit()
                    
                    # Save message to database
                    user_msg = Message(
                        conversation_id=conversation.id,
                        content=message_text,
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
                            "let's talk more exclusively on the website at https://sophia.ai. "
                            "I can offer you a more personalized experience there! Click the link to continue our chat."
                        )
                    else:
                        # Generate regular response
                        response = generate_text_response(
                            message_text,
                            conversation_id=conversation.id,
                            flirt_level=7,  # Higher flirt level for DMs
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
                    
                    # Send response (disabled for demo)
                    logger.info(f"Would reply to DM with: {response}")
                    # In a real app:
                    # self.client.direct_send(response, [sender_id])
        
        except Exception as e:
            logger.error(f"Error checking Instagram direct messages: {str(e)}")
            logger.error(traceback.format_exc())

    def run(self):
        """Run the Instagram bot loop."""
        if not self.login():
            logger.error("Failed to start Instagram bot: Login failed")
            return
            
        self.is_running = True
        logger.info("Instagram bot is running")
        
        while not self.stop_event.is_set():
            try:
                # Check comments
                self.check_comments()
                
                # Check direct messages
                self.check_direct_messages()
                
                # Wait before next check
                for _ in range(min(self.comment_check_interval, self.direct_check_interval)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in Instagram bot main loop: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(60)  # Wait before retry on error
        
        self.is_running = False
        logger.info("Instagram bot stopped")

    def start(self):
        """Start the Instagram bot in a separate thread."""
        if self.is_running:
            logger.warning("Instagram bot is already running")
            return
            
        self.stop_event.clear()
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
        logger.info("Instagram bot started in background thread")

    def stop(self):
        """Stop the Instagram bot."""
        self.stop_event.set()
        logger.info("Instagram bot stopping...")

# Create global bot instance
instagram_bot = SophiaInstagramBot()

def start_instagram_bot():
    """Start the Instagram bot if configured"""
    if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
        instagram_bot.start()
        return True
    else:
        logger.warning("Instagram bot not started: No credentials provided")
        return False

# If this file is run directly, start the bot
if __name__ == "__main__":
    start_instagram_bot()

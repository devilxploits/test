import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to path
sys.path.insert(0, os.path.abspath('.'))

# Import the database and app
from app import app, db

def recreate_database():
    """
    Recreate the database with the updated schema
    """
    with app.app_context():
        logger.info("Dropping all tables...")
        db.drop_all()
        
        logger.info("Creating tables with updated schema...")
        db.create_all()
        
        logger.info("Initializing default settings...")
        from models import SophiaSettings
        
        # Create default settings
        settings = SophiaSettings()
        settings.personality = "flirty, sensual, supportive, playful"
        settings.content_style = "inspirational, seductive, positive, intimate"
        settings.response_length = 150
        settings.flirt_level = 8
        settings.post_frequency = 2
        settings.allow_nsfw = True
        settings.kobold_model = "MythoMax"
        settings.openrouter_api_key = ""
        settings.use_flirt_based_models = True
        settings.default_model = "mythomax-l2"
        settings.mythmax_model = "gryphe/mythomax-l2-13b"
        settings.openhermes_model = "teknium/openhermes-2.5-mistral"
        settings.deepseek_model = "deepseek-ai/deepseek-chat-7b"
        settings.sd_url = ""
        settings.sd_model = "RealisticVision"
        settings.sd_negative_prompt = "deformed, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands"
        settings.sd_steps = 30
        settings.sd_cfg_scale = 7.0
        settings.sd_width = 1024
        settings.sd_height = 1024
        settings.enable_voice_calls = True
        settings.use_webrtc = True
        settings.use_tts = True
        settings.tts_voice_id = "female_sensual"
        settings.tts_speed = 0.9
        settings.subscription_fee = 9.99
        settings.paypal_settings = '{"business_email": "", "client_id": "", "client_secret": "", "environment": "sandbox"}'
        settings.instagram_settings = '{"hashtag_count": 5, "emoji_level": "medium"}'
        settings.telegram_settings = '{"use_stickers": true, "auto_reply": true}'
        
        db.session.add(settings)
        db.session.commit()
        
        logger.info("Database initialized successfully")

if __name__ == "__main__":
    recreate_database()
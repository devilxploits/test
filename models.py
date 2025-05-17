from datetime import datetime
from app import db
# from flask_login import UserMixin
import json

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    is_paid = db.Column(db.Boolean, default=False)  # Premium paid user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Daily limits
    daily_image_limit = db.Column(db.Integer, default=0)  # Free: 0, Paid: 2, Admin: unlimited
    daily_call_minutes = db.Column(db.Integer, default=0)  # Free: 0, Paid: 10, Admin: unlimited
    last_reset_date = db.Column(db.Date, default=datetime.utcnow().date())
    
    # User preferences
    language = db.Column(db.String(10), default="en")
    
    # Relationships
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic')
    
    def can_generate_image(self):
        """Check if user can generate more images today"""
        # Admin has unlimited access
        if self.is_admin:
            return True
            
        # Free users can't generate images
        if not self.is_paid:
            return False
            
        # Reset counters if it's a new day
        today = datetime.utcnow().date()
        if self.last_reset_date != today:
            self.daily_image_limit = 2 if self.is_paid else 0
            self.daily_call_minutes = 10 if self.is_paid else 0
            self.last_reset_date = today
            db.session.commit()
            
        # Check if paid user still has daily quota
        return self.daily_image_limit > 0
        
    def can_make_call(self, minutes=1):
        """Check if user can make voice calls with specified duration"""
        # Admin has unlimited access
        if self.is_admin:
            return True
            
        # Free users can't make calls
        if not self.is_paid:
            return False
            
        # Reset counters if it's a new day
        today = datetime.utcnow().date()
        if self.last_reset_date != today:
            self.daily_image_limit = 2 if self.is_paid else 0
            self.daily_call_minutes = 10 if self.is_paid else 0
            self.last_reset_date = today
            db.session.commit()
            
        # Check if paid user still has daily quota
        return self.daily_call_minutes >= minutes
    
    def __repr__(self):
        return f'<User {self.username}>'


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    source = db.Column(db.String(20), default="website")  # website, instagram, telegram
    external_id = db.Column(db.String(128), nullable=True)  # External user ID for social platforms
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Store detected language
    detected_language = db.Column(db.String(10), default="en")
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy='dynamic')
    
    def __repr__(self):
        return f'<Conversation {self.id} from {self.source}>'


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_from_user = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id} {"from user" if self.is_from_user else "from Sophia"}>'


class ContentPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    caption = db.Column(db.Text)
    hashtags = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    image_prompt = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_for = db.Column(db.DateTime, nullable=True)
    published_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="draft")  # draft, scheduled, published, failed
    
    # Content type (image, reel, video)
    content_type = db.Column(db.String(20), default="image")
    
    # Path to media assets (for videos/reels)
    media_path = db.Column(db.String(500), nullable=True)
    
    # Platform targeting
    platforms = db.Column(db.String(100), default="instagram,telegram")  # Comma-separated list
    
    # Error information if publishing failed
    error_message = db.Column(db.Text, nullable=True)
    
    def get_platforms(self):
        return self.platforms.split(',')
    
    def set_platforms(self, platform_list):
        self.platforms = ','.join(platform_list)
    
    def __repr__(self):
        return f'<ContentPost {self.id} status={self.status}>'


class SophiaSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    personality = db.Column(db.Text, default='flirty, sensual, supportive, playful')
    content_style = db.Column(db.Text, default='inspirational, seductive, positive, intimate')
    response_length = db.Column(db.Integer, default=150)  # Slightly longer responses
    flirt_level = db.Column(db.Integer, default=8)  # Scale 1-10, set to high by default
    
    # Social media posting settings
    post_frequency = db.Column(db.Integer, default=2)  # Total posts per day
    images_per_day = db.Column(db.Integer, default=1)  # Number of image posts per day
    reels_per_day = db.Column(db.Integer, default=1)  # Number of reel/video posts per day
    post_time_start = db.Column(db.Integer, default=9)  # Starting hour for posts (9 AM)
    post_time_end = db.Column(db.Integer, default=21)  # Ending hour for posts (9 PM)
    post_days = db.Column(db.String(20), default="0,1,2,3,4,5,6")  # Days to post (0=Monday, 6=Sunday)
    
    # AI model settings
    allow_nsfw = db.Column(db.Boolean, default=True)  # Allow NSFW content generation
    
    # OpenRouter API settings for Chat and Calls
    openrouter_api_key = db.Column(db.String(200), default='')  # OpenRouter API key
    use_flirt_based_models = db.Column(db.Boolean, default=True)  # Select models based on flirt level
    
    # Chat models
    default_model = db.Column(db.String(100), default='gryphe/mythomax-l2-13b')  # Default model (MythoMax-L2)
    mythomax_model = db.Column(db.String(100), default='gryphe/mythomax-l2-13b')  # High flirt level model
    openhermes_model = db.Column(db.String(100), default='teknium/openhermes-2.5-mistral')  # Medium flirt level model
    deepseek_model = db.Column(db.String(100), default='deepseek-ai/deepseek-chat-7b-nsfw')  # NSFW model
    
    # Speech-to-Text models
    whisper_api_key = db.Column(db.String(200), default='')  # Whisper API key
    whisper_model = db.Column(db.String(100), default='whisper-1')  # Whisper model
    
    # Text-to-Speech models
    tts_provider = db.Column(db.String(100), default='piper')  # TTS provider (Piper)
    piper_voice_id = db.Column(db.String(100), default='female_natural')  # Voice ID for Piper
    tts_speed = db.Column(db.Float, default=0.9)  # Slightly slower for more natural feel
    
    # WebRTC settings for calls
    enable_voice_calls = db.Column(db.Boolean, default=True)  # Enable voice calls
    use_webrtc = db.Column(db.Boolean, default=True)  # Use WebRTC for voice calls
    webrtc_config = db.Column(db.Text, default='{"ice_servers": [{"urls": "stun:stun.l.google.com:19302"}]}')  # WebRTC config
    
    # Image Generation settings (Google Colab + Stable Diffusion)
    # Stable Diffusion API settings
    sd_url = db.Column(db.String(200), default='')  # URL to Stable Diffusion API (Automatic1111)
    sd_model = db.Column(db.String(100), default='RealisticVision')  # Default image model
    sd_negative_prompt = db.Column(db.Text, default='deformed, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands')
    sd_steps = db.Column(db.Integer, default=30)  # Number of sampling steps
    sd_cfg_scale = db.Column(db.Float, default=7.0)  # Guidance scale
    sd_width = db.Column(db.Integer, default=1024)  # Image width
    sd_height = db.Column(db.Integer, default=1024)  # Image height
    
    # Google Colab settings
    colab_notebook_url = db.Column(db.String(200), default='')  # URL to Google Colab notebook
    colab_api_key = db.Column(db.String(200), default='')  # API key for Google Colab
    
    # Payment settings
    subscription_fee = db.Column(db.Float, default=9.99)  # Monthly subscription fee in USD
    paypal_settings = db.Column(db.Text, default='{"business_email": "", "client_id": "", "client_secret": "", "environment": "sandbox"}')
    
    # Social media settings as JSON
    instagram_settings = db.Column(db.Text, default='{"hashtag_count": 5, "emoji_level": "medium"}')
    telegram_settings = db.Column(db.Text, default='{"use_stickers": true, "auto_reply": true}')
    
    # Get and set methods for JSON fields
    def get_instagram_settings(self):
        return json.loads(self.instagram_settings)
    
    def set_instagram_settings(self, settings_dict):
        self.instagram_settings = json.dumps(settings_dict)
    
    def get_telegram_settings(self):
        return json.loads(self.telegram_settings)
    
    def set_telegram_settings(self, settings_dict):
        self.telegram_settings = json.dumps(settings_dict)
        
    def get_paypal_settings(self):
        return json.loads(self.paypal_settings)
    
    def set_paypal_settings(self, settings_dict):
        self.paypal_settings = json.dumps(settings_dict)
    
    def __repr__(self):
        return f'<SophiaSettings {self.id}>'

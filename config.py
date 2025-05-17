import os

class Config:
    # Flask config
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'sophia_dev_key')
    
    # Database config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///sophia.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API credentials
    STABILITY_API_KEY = os.environ.get('STABILITY_API_KEY', '')
    HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    KOBOLD_HORDE_API_KEY = os.environ.get('KOBOLD_HORDE_API_KEY', '')
    PIPER_TTS_API_KEY = os.environ.get('PIPER_TTS_API_KEY', '')
    
    # Local Stable Diffusion setup (for your local machine)
    # URL to AUTOMATIC1111 webui API - uncomment and set when running on your own machine
    # SD_URL = "http://localhost:7860"  # Default AUTOMATIC1111 port
    # SD_MODEL = "realisticVisionV51_v51VAE.safetensors"  # Or other recommended model
    
    # Instagram credentials
    INSTAGRAM_USERNAME = os.environ.get('INSTAGRAM_USERNAME', '')
    INSTAGRAM_PASSWORD = os.environ.get('INSTAGRAM_PASSWORD', '')
    
    # Telegram credentials
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    
    # Sophia AI settings
    DEFAULT_LANGUAGE = 'en'
    SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'it', 'ru', 'zh', 'ja', 'ko', 'ar']
    
    # LLM settings
    TEXT_GENERATION_MODEL = os.environ.get('TEXT_GENERATION_MODEL', 'google/flan-t5-base')
    TEXT_EMBEDDING_MODEL = os.environ.get('TEXT_EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # Content generation settings
    MAX_CONTENT_LENGTH = 2000
    MIN_CONTENT_LENGTH = 50
    IMAGE_SIZE = "1024x1024"
    
    # URL for the app (used in social media links)
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
    
    # Path to stock photos - these are fallbacks when image generation is unavailable
    STOCK_PHOTOS = {
        'portraits': [
            "/static/assets/portraits/portrait1.jpg",
            "/static/assets/portraits/portrait2.jpg",
            "/static/assets/portraits/portrait3.jpg",
            "/static/assets/portraits/portrait4.jpg",
            "/static/assets/portraits/portrait5.jpg",
            "/static/assets/portraits/portrait6.jpg",
            "/static/assets/portraits/portrait7.jpg",
            "/static/assets/portraits/portrait8.jpg"
        ],
        'lifestyle': [
            "/static/assets/lifestyle/lifestyle1.jpg",
            "/static/assets/lifestyle/lifestyle2.jpg",
            "/static/assets/lifestyle/lifestyle3.jpg",
            "/static/assets/lifestyle/lifestyle4.jpg",
            "/static/assets/lifestyle/lifestyle5.jpg",
            "/static/assets/lifestyle/lifestyle6.jpg"
        ]
    }
    
    # Sophia's appearance & personality (for consistency across generated content)
    SOPHIA_APPEARANCE = {
        'features': ['blonde hair', 'blue eyes', 'attractive features'],
        'styles': ['glamorous', 'natural', 'casual', 'elegant', 'playful'],
        'expressions': ['happy', 'smiling', 'flirty', 'thoughtful', 'excited', 'surprised', 'confident']
    }
    
    # Sophia's personality traits (used for content generation)
    SOPHIA_PERSONALITY = {
        'traits': ['friendly', 'empathetic', 'intelligent', 'creative', 'flirty', 'supportive', 'expressive'],
        'interests': ['technology', 'art', 'music', 'travel', 'fitness', 'food', 'fashion', 'books', 'photography'],
        'tone': ['positive', 'uplifting', 'warm', 'playful', 'enthusiastic', 'passionate']
    }
    
    # Stable Diffusion recommended settings for realistic portraits - uncensored version
    SD_SETTINGS = {
        'default_model': 'stable-diffusion-webui-automatic1111-realisticvision',  # AUTOMATIC1111 with RealisticVision model
        'sampling_steps': 45,  # Higher steps for better quality
        'sampler': 'DPM++ SDE Karras',  # Best sampler for photorealism
        'cfg_scale': 7.0,  # Lower cfg for more natural results 
        'size': '1024x1024',  # High resolution for detail
        'consistency_prompt': 'a stunningly beautiful woman with blonde hair, blue eyes, perfect facial features, fit athletic body with curves, sultry pose, bedroom setting, highly photorealistic, uncensored, RealisticVision, high quality professional photography, ultra detailed, perfect lighting, flawless skin, magazine quality, RAW photo',
        'uncensored': True,  # Allow uncensored content
        'use_colab_gpu': True,  # Always use Google Colab's GPU resources
        'colab_gpu_type': 'T4',  # Use T4 GPU on Google Colab
        'webui': 'AUTOMATIC1111'  # Use AUTOMATIC1111 web UI
    }

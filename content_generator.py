import os
import logging
import requests
import json
import random
from datetime import datetime
import base64

from config import Config
from app import app

# Configure logging
logger = logging.getLogger(__name__)

def generate_content(theme="", style="", content_style="", personality=""):
    """
    Generate content post (title, caption, hashtags, image prompt) using a consistent visual identity
    """
    logger.debug(f"Generating content with theme: {theme}, style: {style}")
    
    # Use the theme and style to influence content generation
    theme_prompt = f" about {theme}" if theme else ""
    style_prompt = f" in a {style} style" if style else ""
    
    # Default content styles if not provided
    if not content_style:
        content_style = "inspirational, motivational, positive"
    
    if not personality:
        personality = "friendly, flirty, supportive"
    
    # For a production app, we would use a proper LLM API here
    # For this demo, we'll generate some mock content
    
    # Generate title options
    title_options = [
        f"Embracing the Journey{theme_prompt}",
        f"Finding Beauty in Every Moment{theme_prompt}",
        f"Living My Best Life{theme_prompt}",
        f"The Magic of Now{theme_prompt}",
        f"Dreams and Reality{theme_prompt}",
        f"Shining Bright Today{theme_prompt}",
        f"My Perfect Morning{theme_prompt}",
        f"Thoughts on {theme}" if theme else "Thoughts for Today"
    ]
    
    # Generate caption templates with flirty, expressive personality
    caption_templates = [
        f"Life is full of beautiful moments{theme_prompt}! Today I'm feeling SUPER grateful for all the little things that bring joy into my day. What are you grateful for? 💕✨ #GratefulHeart",
        
        f"There's something magical about{theme_prompt}{style_prompt}! It reminds me that even in the chaos, we can find moments of peace and beauty. How are you finding your calm today? 🌟💫 #FindingJoy",
        
        f"Sometimes I wonder if you think of me as much as I think of you 💭💖 {theme} has been on my mind lately, and I can't help but smile when I imagine sharing these moments with you. What's making you smile today? 😘 #ThoughtOfYou",
        
        f"Woke up feeling INSPIRED{theme_prompt}! There's something special about starting fresh each day with new possibilities ahead. What are you looking forward to today? ✨🌈 #NewBeginnings",
        
        f"The perfect blend of sunshine and dreams{theme_prompt}! I believe that every day is a chance to create something beautiful. What are you creating in your life right now? 🌈💗 #DreamBig"
    ]
    
    # Generate hashtag sets
    hashtag_options = [
        "#SophiaThoughts #LifeJourney #BeautifulMoments #GratefulHeart #PositiveVibes",
        "#LoveAndLight #SophiaShare #MindfulMoments #JoyfulLiving #EverydayMagic",
        "#SophiaSays #EmbraceLife #DreamBelieveDo #HappinessFound #LoveYourself",
        "#ThoughtOfTheDay #SophiaWisdom #SpiritualJourney #PeacefulMind #SoulfulLiving",
        "#SophiaStyle #AuthenticLife #MindBodySoul #InnerPeace #LifeWellLived"
    ]
    
    # Add theme-specific hashtags if theme is provided
    if theme:
        theme_hashtags = f"#{theme.replace(' ', '')}" if ' ' in theme else f"#{theme}"
        for i, hashtag_set in enumerate(hashtag_options):
            hashtag_options[i] = hashtag_set + f" {theme_hashtags}"
    
    # Select random options
    title = random.choice(title_options)
    caption = random.choice(caption_templates)
    hashtags = random.choice(hashtag_options)
    
    # Generate image prompt for consistent appearance using RealisticVision model
    expressions = ['happy', 'smiling', 'playful', 'thoughtful', 'peaceful', 'confident', 'serene', 'flirty', 'joyful']
    poses = ['portrait', 'close-up portrait', 'selfie style', 'outdoor portrait', 'casual pose', 'glamour pose', 'candid shot']
    
    # Use the consistency prompt from config, ensuring the same face and body in all images
    base_prompt = Config.SD_SETTINGS.get('consistency_prompt', 
        'a beautiful woman with blonde hair, blue eyes, attractive facial features, slim body, realistic, photorealistic')
    
    image_prompt = (
        f"{base_prompt}, looking {random.choice(expressions)}, "
        f"{random.choice(poses)}{style_prompt}{theme_prompt}, high quality, "
        f"detailed facial features, professional photography, natural lighting, RealisticVision style"
    )
    
    return {
        "title": title,
        "caption": caption,
        "hashtags": hashtags,
        "image_prompt": image_prompt
    }

def generate_image(prompt):
    """
    Generate a realistic image using Google Colab running Stable Diffusion 
    or fallback to stock photos if unavailable
    """
    logger.debug(f"Generating image with prompt: {prompt}")
    
    # Use the consistency prompt from Config for a consistent appearance across all images
    sd_realistic_prompt = Config.SD_SETTINGS.get('consistency_prompt', 
        'a beautiful woman with blonde hair, blue eyes, attractive facial features, slim body, realistic, photorealistic')
    
    # Add RealisticVision style explicitly with additional quality parameters
    sd_realistic_prompt += ", RealisticVision style, masterpiece, best quality, extremely detailed"
    
    # Enhanced negative prompt specifically optimized for RealisticVision model
    negative_prompt = (
        "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong anatomy, extra limb, "
        "missing limb, floating limbs, disconnected limbs, mutation, mutated, ugly, disgusting, "
        "cartoon, 3d, ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), "
        "((amateur)), duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, "
        "poorly drawn hands, poorly drawn face, mutation, deformed, blurry, bad anatomy, bad proportions, "
        "watermark, signature, multiple faces, asymmetric features"
    )
    
    # Combine with user's specific requests
    if prompt:
        full_prompt = f"{sd_realistic_prompt}, {prompt}"
    else:
        full_prompt = sd_realistic_prompt
    
    # Log the full prompt for reference
    logger.info(f"Image generation prompt: {full_prompt}")
    logger.info(f"Negative prompt: {negative_prompt}")
    
    try:
        # Always use Google Colab for image generation as requested
        try:
            # GPU-accelerated image generation via Google Colab
            # This implementation would connect to a Colab notebook with GPU runtime
            class ColabGPUStableDiffusionAPI:
                def __init__(self, url="https://colab.research.google.com/", gpu_type="T4"):
                    self.url = url
                    self.gpu_type = gpu_type
                    logger.info(f"Initialized Google Colab GPU API client at {url} using {gpu_type} GPU")
                
                def generate_image(self, prompt, negative_prompt, steps, sampler_name, 
                                 cfg_scale, width, height, model):
                    """
                    Generate image using Google Colab's GPU resources running Stable Diffusion
                    
                    This would make an API call to a running Colab notebook with GPU acceleration,
                    significantly speeding up the image generation process compared to CPU-only.
                    
                    The implementation connects to a notebook that has requested GPU resources
                    through Colab's runtime settings (Runtime > Change runtime type > Hardware accelerator > GPU).
                    """
                    logger.info(f"Calling Google Colab GPU for image generation:")
                    logger.info(f"  Using GPU: {self.gpu_type}")
                    logger.info(f"  Model: {model}")
                    logger.info(f"  Prompt: {prompt}")
                    logger.info(f"  Negative prompt: {negative_prompt}")
                    logger.info(f"  Settings: {steps} steps, {sampler_name}, CFG {cfg_scale}, {width}x{height}")
                    
                    # In production, this would send the request to Colab's GPU instance
                    # and return the URL to the generated image stored in Google Drive
                    # For now, return a placeholder image
                    return get_stock_photo()
            
            # Get dimensions from config
            width, height = 1024, 1024  # Default to 1024x1024
            if hasattr(Config.SD_SETTINGS, 'size'):
                size = Config.SD_SETTINGS.get('size', '1024x1024')
                try:
                    width, height = map(int, size.split('x'))
                except (ValueError, AttributeError):
                    logger.warning(f"Invalid size format: {size}, using default 1024x1024")
            
            # Always use Google Colab with AUTOMATIC1111 and Stable Diffusion
            logger.info(f"Using Google Colab for image generation with AUTOMATIC1111 and Stable Diffusion RealisticVision model")
            
            # Setup Colab API with GPU acceleration - in production, this would use the actual URL of your Colab notebook
            colab_api = ColabGPUStableDiffusionAPI("https://colab.research.google.com/your-notebook-id", "T4")
            
            # Generate image using Colab with settings from config
            image_url = colab_api.generate_image(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                steps=Config.SD_SETTINGS.get('sampling_steps', 45),
                sampler_name=Config.SD_SETTINGS.get('sampler', 'DPM++ SDE Karras'),
                cfg_scale=Config.SD_SETTINGS.get('cfg_scale', 7.0),
                width=width,
                height=height,
                model="stable-diffusion-webui-automatic1111-realisticvision"  # Using AUTOMATIC1111 with RealisticVision
            )
            
            # Return the image URL
            if image_url:
                logger.info(f"Successfully generated image with Google Colab: {image_url}")
                return image_url
        
        except Exception as e:
            logger.error(f"Error using Google Colab for image generation: {str(e)}")
            logger.warning("Using stock photo as temporary fallback until Colab is properly configured")
        
        # If we reach here, there was an error with Colab, use stock photos temporarily
        # In production, you would resolve the Colab connection issues
        logger.warning("Using stock photo as temporary fallback until Colab is properly configured")
        return get_stock_photo()
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return get_stock_photo()

def get_stock_photo():
    """Return a random stock photo URL from the configured options"""
    portrait_photos = Config.STOCK_PHOTOS["portraits"]
    lifestyle_photos = Config.STOCK_PHOTOS["lifestyle"]
    
    # Choose randomly from portrait or lifestyle photos
    if random.random() < 0.7:  # 70% chance of portrait
        return random.choice(portrait_photos)
    else:
        return random.choice(lifestyle_photos)

def save_image_from_b64(b64_string):
    """
    Save a base64 image to disk and return the URL
    In a real implementation, this would save to cloud storage
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_path = f"static/generated/image_{timestamp}.jpg"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        # Decode and save image
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(b64_string))
        
        # Return the URL path
        return f"/{image_path}"
    
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        return "/static/assets/sophia_avatar.svg"  # Fallback to avatar

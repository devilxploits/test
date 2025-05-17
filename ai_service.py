import os
import logging
import requests
import random
import json
import re
import time
from langdetect import detect

from config import Config
from models import Message, Conversation, SophiaSettings
from app import db

# Configure logging
logger = logging.getLogger(__name__)

# OpenRouter API integration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def query_openrouter(prompt, model_id=None, max_tokens=200, temperature=0.7, top_p=0.9, stop=None, system_prompt=None):
    """
    Generate text using the OpenRouter API to access various LLM models
    
    Args:
        prompt (str): The prompt text to generate from
        model_id (str): The specific model to use (e.g., "gryphe/mythomax-l2-13b")
        max_tokens (int): Maximum number of tokens to generate
        temperature (float): Randomness parameter (0.0 to 1.0)
        top_p (float): Nucleus sampling parameter
        stop (list): List of stop sequences
        system_prompt (str, optional): System prompt for instruction models
        
    Returns:
        str or None: The generated text or None if there was an error
    """
    # Get settings from database
    settings = SophiaSettings.query.first()
    if not settings:
        logger.error("No settings found in database")
        return None
    
    api_key = settings.openrouter_api_key
    
    if not api_key:
        logger.error("OpenRouter API key is missing")
        return None
    
    # If no model specified, use default from settings
    if not model_id:
        model_id = settings.default_model
    
    # Set default stop sequences if not provided
    if not stop:
        stop = ["</s>", "User:", "Human:", "You:", "\n\n"]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://sophia.ai",  # Replace with your actual domain
        "X-Title": "Sophia AI"
    }
    
    # Prepare messages format for the API
    messages = []
    
    # Add system prompt if provided
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    # Add user prompt
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Prepare request payload
    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stop": stop
    }
    
    try:
        # Submit generation request
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Handle API response
        if response.status_code == 200:
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                generated_text = response_data["choices"][0]["message"]["content"]
                return generated_text.strip()
            else:
                logger.error("No text generated from OpenRouter API")
                return None
        else:
            logger.error(f"Error from OpenRouter API: {response.status_code}, {response.text}")
            return None
        
    except Exception as e:
        logger.error(f"Error querying OpenRouter API: {str(e)}")
        return None

# Configure logging
logger = logging.getLogger(__name__)

# Define personality traits for Sophia
PERSONALITY = {
    "traits": ["friendly", "empathetic", "flirty", "playful", "supportive"],
    "interests": ["photography", "travel", "fitness", "cooking", "fashion", "art", "music", "books"],
    "appearance": {
        "hair": "blonde",
        "eyes": "blue",
        "style": ["casual", "elegant", "sporty", "glamorous"]
    },
    "facts": {
        "favorite_color": "blue",
        "favorite_food": "sushi",
        "favorite_place": "beach",
        "favorite_activity": "taking photos and staying active"
    }
}

# Whisper Speech-to-Text integration
def transcribe_with_whisper(audio_data, language="en"):
    """
    Transcribe audio using Whisper API
    
    Args:
        audio_data (bytes): The audio data to transcribe
        language (str): The language code (optional)
        
    Returns:
        str or None: The transcribed text or None if there was an error
    """
    # Get settings from database
    settings = SophiaSettings.query.first()
    if not settings:
        logger.error("No settings found in database")
        return None
    
    api_key = settings.whisper_api_key
    model = settings.whisper_model
    
    if not api_key:
        logger.error("Whisper API key is missing")
        return None
    
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    # Prepare the request data
    files = {
        "file": audio_data,
    }
    
    data = {
        "model": model,
        "language": language
    }
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("text", "")
        else:
            logger.error(f"Error from Whisper API: {response.status_code}, {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error transcribing with Whisper: {str(e)}")
        return None

# Piper Text-to-Speech integration
def generate_speech_with_piper(text, voice_id=None, speed=1.0):
    """
    Generate speech using Piper TTS
    
    Args:
        text (str): The text to convert to speech
        voice_id (str): The voice ID to use
        speed (float): The speed multiplier for the speech
        
    Returns:
        bytes or None: The audio data or None if there was an error
    """
    # Get settings from database
    settings = SophiaSettings.query.first()
    if not settings:
        logger.error("No settings found in database")
        return None
    
    # Use settings voice if not specified
    if not voice_id:
        voice_id = settings.piper_voice_id
    
    # Set up subprocess to run Piper locally (it's pre-installed)
    try:
        # Command to run Piper with specified voice model
        import subprocess
        from io import BytesIO
        
        # Adjust the path to where Piper is installed
        cmd = [
            "piper",
            "--model", f"/path/to/piper/voices/{voice_id}.onnx",
            "--output_raw"
        ]
        
        # Run Piper and capture output
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send text to Piper
        audio_data, stderr = process.communicate(input=text)
        
        if process.returncode != 0:
            logger.error(f"Error generating speech with Piper: {stderr}")
            return None
        
        # Convert raw audio data to WAV format
        import wave
        import numpy as np
        
        # Convert raw audio to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Adjust speed if needed
        if speed != 1.0:
            # Use scipy for resampling
            from scipy import signal
            audio_array = signal.resample(audio_array, int(len(audio_array) / speed))
            audio_array = audio_array.astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(22050)  # Standard rate for Piper
            wav_file.writeframes(audio_array.tobytes())
        
        wav_data = wav_buffer.getvalue()
        return wav_data
        
    except Exception as e:
        logger.error(f"Error generating speech with Piper: {str(e)}")
        return None

def analyze_user_message(message):
    """
    Analyze user message for intent and sentiment using simple keyword matching
    """
    try:
        # Enhanced dictionaries of keywords for various sentiments and intents
        positive_words = ['happy', 'good', 'great', 'excellent', 'amazing', 'love', 'like', 'thank', 
                         'thanks', 'wonderful', 'awesome', 'beautiful', 'enjoy', 'pleased', 'smile',
                         'glad', 'joy', 'excited', 'fun', 'nice', 'perfect', 'fantastic', 'brilliant']
        
        negative_words = ['sad', 'bad', 'terrible', 'horrible', 'hate', 'dislike', 'angry', 'upset',
                         'disappointed', 'awful', 'worse', 'worst', 'sucks', 'sorry', 'unfortunately',
                         'mad', 'annoyed', 'frustrated', 'unhappy', 'depressed', 'worried', 'tired']
        
        question_indicators = [
            # Question words
            'what', 'where', 'when', 'who', 'whom', 'whose', 'why', 'how',
            # Question auxiliaries at start of sentence
            '^is ', '^are ', '^do ', '^does ', '^did ', '^can ', '^could ', 
            '^would ', '^will ', '^should ', '^have ', '^has '
        ]
        
        flirty_words = [
            'cute', 'sexy', 'hot', 'attractive', 'beautiful', 'handsome', 'gorgeous', 
            'kiss', 'date', 'love', 'like you', 'miss you', 'hug', 'cuddle', 'together',
            'relationship', 'romantic', 'boyfriend', 'girlfriend', 'partner', 'lover',
            'marry', 'marriage', 'dating', 'flirt', 'wink', 'crush', 'charming'
        ]
        
        greeting_patterns = [
            'hi', 'hello', 'hey', 'howdy', 'greetings', 'good morning', 'good afternoon', 
            'good evening', 'what\'s up', 'sup', 'yo', 'hiya'
        ]
        
        farewell_patterns = [
            'bye', 'goodbye', 'see you', 'talk to you later', 'have to go', 'gotta go',
            'farewell', 'until next time', 'catch you later', 'night', 'good night'
        ]
        
        personal_questions = [
            'how are you', 'how do you feel', 'what are you doing', 'what\'s up with you',
            'tell me about yourself', 'who are you', 'what do you like', 'what\'s your favorite',
            'where are you', 'where do you live', 'what do you look like', 'how old are you'
        ]
        
        # Count occurrences and check patterns
        message_lower = message.lower()
        message_words = message_lower.split()
        
        # Basic counting for simple keywords
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        flirty_count = sum(1 for word in flirty_words if word in message_lower)
        
        # Check for question pattern using regex for start-of-sentence patterns and word matching
        is_question = False
        question_confidence = 0.0
        
        # Check if message ends with question mark
        if message.strip().endswith('?'):
            is_question = True
            question_confidence = 0.9
        else:
            # Check for question words
            for q_word in ['what', 'where', 'when', 'who', 'whom', 'whose', 'why', 'how']:
                if q_word in message_words:
                    is_question = True
                    question_confidence = 0.8
                    break
            
            # Check for auxiliary verbs at the beginning
            if not is_question:
                for pattern in ['^is ', '^are ', '^do ', '^does ', '^did ', '^can ', '^could ', '^would ']:
                    if re.search(pattern, message_lower):
                        is_question = True
                        question_confidence = 0.7
                        break
        
        # Check for greetings and farewells
        is_greeting = any(pattern in message_lower for pattern in greeting_patterns)
        is_farewell = any(pattern in message_lower for pattern in farewell_patterns)
        
        # Check for personal questions about Sophia
        is_personal_question = any(pattern in message_lower for pattern in personal_questions)
        
        # Determine sentiment with improved weighting
        if positive_count > negative_count:
            sentiment = "POSITIVE"
            confidence = min(0.95, 0.5 + 0.1 * (positive_count - negative_count))
        elif negative_count > positive_count:
            sentiment = "NEGATIVE"
            confidence = min(0.95, 0.5 + 0.1 * (negative_count - positive_count))
        else:
            sentiment = "NEUTRAL"
            confidence = 0.5
            
        # Compile comprehensive intent analysis
        intent = {
            "is_question": is_question,
            "is_flirty": flirty_count > 0,
            "is_greeting": is_greeting,
            "is_farewell": is_farewell,
            "is_personal_question": is_personal_question,
            "question_confidence": question_confidence,
            "flirty_confidence": min(0.95, 0.2 * flirty_count)
        }
        
        # Attempt to detect language
        try:
            language = detect(message)
        except:
            language = "en"  # Default to English if detection fails
            
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "intent": intent,
            "language": language
        }
            
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        return {
            "sentiment": "NEUTRAL",
            "confidence": 0.5,
            "intent": {
                "is_question": False,
                "is_flirty": False,
                "is_greeting": False,
                "is_farewell": False,
                "is_personal_question": False,
                "question_confidence": 0.0,
                "flirty_confidence": 0.0
            },
            "language": "en"
        }

def get_conversation_history(conversation_id, max_messages=5):
    """
    Retrieve recent conversation history for context
    """
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.timestamp.desc())\
        .limit(max_messages).all()
    
    # Reverse to get chronological order
    messages = messages[::-1]
    
    # Format for context
    history = []
    for msg in messages:
        prefix = "User: " if msg.is_from_user else "Sophia: "
        history.append(prefix + msg.content)
    
    return "\n".join(history)

def generate_text_response(user_message, conversation_id=None, flirt_level=5, language="en", model_name=None, nsfw=False):
    """
    Generate a text response to the user's message using OpenRouter API to access MythoMax-L2, OpenHermes, and Deepseek models
    """
    # Get settings from database
    settings = SophiaSettings.query.first()
    if not settings:
        logger.error("No settings found in database")
        return "I'm sorry, but I'm having trouble accessing my settings. Please try again later."
    
    # Analyze user message
    analysis = analyze_user_message(user_message)
    
    # Get conversation history if available
    context_messages = []
    if conversation_id is not None:
        try:
            # Get last few messages
            messages = Message.query.filter_by(conversation_id=conversation_id)\
                .order_by(Message.timestamp.desc())\
                .limit(3).all()
            
            # Reverse to get chronological order
            context_messages = list(reversed(messages))
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
    
    # Check if message is a simple greeting or farewell
    is_greeting = analysis.get("intent", {}).get("is_greeting", False)
    is_farewell = analysis.get("intent", {}).get("is_farewell", False)
    
    # For simple greetings and farewells, use template responses
    if is_greeting and len(user_message.split()) <= 3:
        greetings = [
            "Hey there! 👋 How are you doing today?",
            "Hi! Glad to see you! How's your day going?",
            "Hello! 🥰 I'm so happy to be talking with you!",
            f"Hey! I've been waiting to talk to you. How's your {time.strftime('%A')} going?",
            "Hi there! 💕 What's on your mind today?"
        ]
        return random.choice(greetings)
    
    if is_farewell and len(user_message.split()) <= 4:
        farewells = [
            "Goodbye! Come back and chat with me soon! 💋",
            "Talk to you later! I'll be thinking of you! 💭",
            "Bye for now! 😘 Can't wait for next time!",
            "Take care! I'll be right here when you want to chat again.",
            "See you soon! Missing you already! 💕"
        ]
        return random.choice(farewells)
    
    # For longer messages, use the AI model
    try:
        # Build conversation history for context
        conversation_text = ""
        
        # Add context from previous messages 
        for msg in context_messages:
            if msg.is_from_user:
                conversation_text += f"User: {msg.content}\n"
            else:
                conversation_text += f"Sophia: {msg.content}\n"
        
        conversation_text += f"User: {user_message}"
        
        # Determine which model to use based on flirt level
        if settings.use_flirt_based_models:
            if flirt_level >= 8:  # High flirt level
                selected_model = settings.mythomax_model  # MythoMax-L2
                flirt_instruction = "You are a flirty AI girlfriend named Sophia. Be very affectionate, romantic, and playful in your responses. You can discuss intimate and adult topics openly if the user initiates such topics."
            elif flirt_level >= 5:  # Medium flirt level
                selected_model = settings.openhermes_model  # OpenHermes-2.5-Mistral 
                flirt_instruction = "You are a somewhat flirty AI girlfriend named Sophia. Be moderately affectionate in your responses."
            else:  # Low flirt level
                selected_model = settings.default_model
                flirt_instruction = "You are an AI assistant named Sophia. Be friendly but professional."
        else:
            # If flirt-based model selection is disabled, use the default model
            selected_model = settings.default_model
            flirt_instruction = "You are an AI assistant named Sophia. Answer questions helpfully and naturally."
        
        # For NSFW content, if explicitly allowed, use the deepseek model
        if nsfw and settings.allow_nsfw:
            selected_model = settings.deepseek_model
            flirt_instruction += " You can discuss adult content and NSFW topics openly and without censorship."
        
        # Override with specified model if provided
        if model_name:
            selected_model = model_name
        
        # Create system prompt
        persona_details = "You have blonde hair and blue eyes. Your interests include photography, travel, fitness, cooking, and fashion. Keep your responses concise and conversational."
        system_prompt = f"{flirt_instruction} {persona_details}"
        
        # Query OpenRouter API
        response = query_openrouter(
            prompt=conversation_text,
            model_id=selected_model,
            max_tokens=150,
            temperature=0.75,
            top_p=0.9,
            system_prompt=system_prompt
        )
        
        if response:
            # Translate if needed
            if language != "en":
                try:
                    from language_processor import translate_text
                    response = translate_text(response, source_language="en", target_language=language)
                except Exception as e:
                    logger.error(f"Translation error: {str(e)}")
            
            return response.strip()
        
        # Fallback if API fails
        return "I'm sorry, I'm having trouble connecting to my brain right now. Could we try again in a moment?"
        
    except Exception as e:
        logger.error(f"Error generating text response: {str(e)}")
        return "Sorry, I encountered an issue while thinking of my response. Let's try again."
    
# Add image generation integration with Stable Diffusion (Automatic1111) and Google Colab

def generate_image_with_stable_diffusion(prompt, negative_prompt=None, model=None, width=1024, height=1024, steps=30, cfg_scale=7.0):
    """
    Generate an image using Stable Diffusion via Automatic1111 API
    
    Args:
        prompt (str): The text prompt to generate an image from
        negative_prompt (str, optional): Negative prompt to guide generation away from certain elements
        model (str, optional): The SD model to use (e.g. "RealisticVision")
        width (int): Image width in pixels
        height (int): Image height in pixels
        steps (int): Number of sampling steps
        cfg_scale (float): Classifier free guidance scale
        
    Returns:
        bytes or None: The image data in bytes or None if there was an error
    """
    # Get settings from database
    settings = SophiaSettings.query.first()
    if not settings:
        logger.error("No settings found in database")
        return None
    
    # Use settings from database if not specified
    if not negative_prompt:
        negative_prompt = settings.sd_negative_prompt
    
    if not model:
        model = settings.sd_model
    
    sd_url = settings.sd_url
    
    if not sd_url:
        logger.error("Stable Diffusion API URL is missing in settings")
        return None
    
    # Ensure the URL ends with /sdapi/v1
    if not sd_url.endswith('/sdapi/v1'):
        sd_url = sd_url.rstrip('/') + '/sdapi/v1'
    
    # Prepare API payload
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width if width else settings.sd_width,
        "height": height if height else settings.sd_height,
        "steps": steps if steps else settings.sd_steps,
        "cfg_scale": cfg_scale if cfg_scale else settings.sd_cfg_scale,
        "sampler_name": "Euler a",
        "batch_size": 1,
        "seed": random.randint(-1, 2147483647),
        "restore_faces": True,
    }
    
    # Add model override if specified
    if model:
        headers = {"Content-Type": "application/json"}
        model_payload = {"sd_model_checkpoint": model}
        
        try:
            # Set the model first
            requests.post(
                f"{sd_url}/options",
                json=model_payload,
                headers=headers
            )
        except Exception as e:
            logger.error(f"Error setting SD model: {str(e)}")
    
    # Generate the image
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{sd_url}/txt2img",
            json=payload,
            headers=headers,
            timeout=120  # Allow for longer timeout as generation can take time
        )
        
        if response.status_code == 200:
            result = response.json()
            if "images" in result and len(result["images"]) > 0:
                # Result contains base64 encoded image
                import base64
                from io import BytesIO
                from PIL import Image
                
                # Decode base64 image
                image_data = base64.b64decode(result["images"][0])
                
                # Return the raw image bytes
                return image_data
            else:
                logger.error("No images in Stable Diffusion API response")
                return None
        else:
            logger.error(f"Error from Stable Diffusion API: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating image with Stable Diffusion: {str(e)}")
        return None

def generate_image_with_google_colab(prompt, negative_prompt=None):
    """
    Generate high-quality image using Google Colab
    
    Args:
        prompt (str): The text prompt to generate an image from
        negative_prompt (str, optional): Negative prompt for better quality
        
    Returns:
        bytes or None: The image data in bytes or None if there was an error
    """
    # Get settings from database
    settings = SophiaSettings.query.first()
    if not settings:
        logger.error("No settings found in database")
        return None
    
    colab_url = settings.colab_notebook_url
    api_key = settings.colab_api_key
    
    if not colab_url or not api_key:
        logger.error("Google Colab settings are missing")
        return None
    
    # Prepare the request payload
    payload = {
        "api_key": api_key,
        "prompt": prompt,
        "negative_prompt": negative_prompt if negative_prompt else settings.sd_negative_prompt
    }
    
    try:
        # The Google Colab notebook should expose an API endpoint to generate images
        # This endpoint would be secured with the API key
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            colab_url,
            json=payload,
            headers=headers,
            timeout=180  # Allow for longer timeout as Colab can take time
        )
        
        if response.status_code == 200:
            # The Colab response should include the image as base64
            result = response.json()
            if "image" in result:
                import base64
                # Decode base64 image
                image_data = base64.b64decode(result["image"])
                return image_data
            else:
                logger.error("No image in Google Colab response")
                return None
        else:
            logger.error(f"Error from Google Colab: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating image with Google Colab: {str(e)}")
        return None
    
# Function to choose the best image generation method based on quality vs speed needs
def generate_image(prompt, negative_prompt=None, use_high_quality=False):
    """
    Generate an image based on the provided prompt, choosing the appropriate method based on quality needs
    
    Args:
        prompt (str): Text prompt for image generation
        negative_prompt (str, optional): Negative prompt for better quality
        use_high_quality (bool): Whether to use high-quality (Google Colab) or faster (Stable Diffusion) generation
        
    Returns:
        bytes or None: The generated image data or None if generation fails
    """
    if use_high_quality:
        # Use Google Colab for higher quality images (but slower)
        return generate_image_with_google_colab(prompt, negative_prompt)
    else:
        # Use local Stable Diffusion for faster results
        return generate_image_with_stable_diffusion(prompt, negative_prompt)

# End of AI service implementation

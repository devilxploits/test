import os
import requests
import logging
import json
import base64
import tempfile
from pathlib import Path

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Define Piper TTS API endpoint
PIPER_API_BASE_URL = "https://api.pipertts.ai/v1"

def add_speech_enhancements(text):
    """
    Enhance text with SSML tags for more sensual, intimate voice output
    
    Args:
        text (str): Original text to be spoken
        
    Returns:
        str: Text with SSML enhancements for more sensual speech
    """
    import re
    
    # Don't process if already contains SSML
    if "<speak>" in text:
        return text
        
    # Wrap in SSML tags
    enhanced = f"<speak>{text}</speak>"
    
    # Add subtle pauses after sentences for more dramatic effect
    enhanced = re.sub(r'([.!?])\s+', r'\1<break time="0.7s"/>', enhanced)
    
    # Add emphasis to certain words that should sound more seductive
    for word in ["love", "like", "want", "need", "feel", "kiss", "touch", "beautiful", "sexy", "hot"]:
        pattern = re.compile(r'\b' + word + r'\b', re.IGNORECASE)
        replacement = f'<prosody rate="0.85" pitch="+10%">{word}</prosody>'
        enhanced = pattern.sub(replacement, enhanced)
    
    # Add breathy quality at special moments
    enhanced = re.sub(r'\b(miss you|thinking of you|want you)\b', 
                     r'<amazon:effect name="breathy"><prosody rate="0.8">\1</prosody></amazon:effect>', 
                     enhanced, 
                     flags=re.IGNORECASE)
    
    # Soften voice for intimate phrases
    intimate_phrases = [
        "just between us", "our little secret", "only for you", 
        "whisper", "secret", "private", "just for you"
    ]
    
    for phrase in intimate_phrases:
        pattern = re.compile(r'\b' + phrase + r'\b', re.IGNORECASE)
        replacement = f'<prosody volume="soft" rate="0.8">{phrase}</prosody>'
        enhanced = pattern.sub(replacement, enhanced)
    
    return enhanced

def generate_speech(text, voice_id="female_sensual", output_format="mp3", speed=0.9, emotional_intensity=1.2, pitch_adjustment=0.1):
    """
    Generate "sexy" speech from text using Piper TTS API
    Enhanced for more sensual and emotional voice output
    
    Args:
        text (str): The text to convert to speech
        voice_id (str): The voice ID to use (default: female_sensual)
        output_format (str): The output format (mp3, wav, ogg)
        speed (float): The speech rate (0.5 to 2.0), slightly slower for more intimate feel
        emotional_intensity (float): Intensity of emotional expression (0.5 to 1.5)
        pitch_adjustment (float): Slight pitch adjustment for more attractive sound (-0.5 to 0.5)
        
    Returns:
        str: Path to the generated audio file, or None if failed
    """
    api_key = Config.PIPER_TTS_API_KEY
    
    if not api_key:
        logger.warning("No Piper TTS API key provided - browser-based TTS will be used as fallback")
        raise ValueError("No Piper TTS API key configured. Please add your API key in the admin settings.")
    
    # Select the best voice for "sexy" output if none specified
    if voice_id == "female_casual":
        voice_id = "female_sensual"  # Default to sensual voice
        
    # Add breathy quality and pauses for more intimate speech
    enhanced_text = add_speech_enhancements(text)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Enhanced payload with additional parameters for more sensual voice
    payload = {
        "text": enhanced_text,
        "voice_id": voice_id,
        "output_format": output_format,
        "speech_rate": speed,
        "pitch_adjustment": pitch_adjustment,
        "emotional_intensity": emotional_intensity,
        "breathiness": 0.4,  # Add breathiness for more intimate sound
        "voice_clarity": 0.9  # Clear but soft voice
    }
    
    try:
        # Make the API request
        response = requests.post(
            f"{PIPER_API_BASE_URL}/tts",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            response_data = response.json()
            audio_content = response_data.get("audio_content")
            
            if audio_content:
                # Decode the base64 audio content
                audio_bytes = base64.b64decode(audio_content)
                
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=f".{output_format}", delete=False
                )
                temp_file.write(audio_bytes)
                temp_file.close()
                
                return temp_file.name
            else:
                logger.error("No audio content in response")
                return None
        else:
            logger.error(f"Error from Piper TTS API: {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        return None

def get_available_voices():
    """
    Get a list of available voices from Piper TTS API
    
    Returns:
        list: A list of available voice IDs
    """
    api_key = Config.PIPER_TTS_API_KEY
    
    if not api_key:
        logger.error("No Piper TTS API key provided")
        return []
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(
            f"{PIPER_API_BASE_URL}/voices",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json().get("voices", [])
        else:
            logger.error(f"Error getting available voices: {response.text}")
            return []
    
    except Exception as e:
        logger.error(f"Error getting available voices: {str(e)}")
        return []
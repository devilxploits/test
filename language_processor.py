import logging
from langdetect import detect, LangDetectException
import time
import random

# Configure logging
logger = logging.getLogger(__name__)

# Language code to name mapping
LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'ru': 'Russian',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'tr': 'Turkish',
    'pl': 'Polish',
    'uk': 'Ukrainian'
}

# Basic translations for common phrases - in a real app, this would use a proper translation API
COMMON_PHRASES = {
    'en': {
        'greeting': 'Hello!',
        'thanks': 'Thank you!',
        'goodbye': 'Goodbye!',
        'love': 'I love you!',
        'miss': 'I miss you!',
        'yes': 'Yes',
        'no': 'No'
    },
    'es': {
        'greeting': '¡Hola!',
        'thanks': '¡Gracias!',
        'goodbye': '¡Adiós!',
        'love': '¡Te quiero!',
        'miss': '¡Te extraño!',
        'yes': 'Sí',
        'no': 'No'
    },
    'fr': {
        'greeting': 'Bonjour!',
        'thanks': 'Merci!',
        'goodbye': 'Au revoir!',
        'love': 'Je t\'aime!',
        'miss': 'Tu me manques!',
        'yes': 'Oui',
        'no': 'Non'
    },
    'de': {
        'greeting': 'Hallo!',
        'thanks': 'Danke!',
        'goodbye': 'Auf Wiedersehen!',
        'love': 'Ich liebe dich!',
        'miss': 'Ich vermisse dich!',
        'yes': 'Ja',
        'no': 'Nein'
    }
}

def detect_language(text):
    """
    Detect the language of a given text
    Returns the language code (e.g., 'en', 'es', 'fr')
    """
    try:
        return detect(text)
    except LangDetectException as e:
        logger.error(f"Language detection error: {str(e)}")
        return 'en'  # Default to English on error

def get_language_name(lang_code):
    """
    Get the full name of a language from its code
    """
    return LANGUAGE_NAMES.get(lang_code, 'Unknown')

def translate_text(text, source_language=None, target_language='en'):
    """
    Translate text from source language to target language
    In a real implementation, this would use a proper translation API
    """
    logger.debug(f"Translating from {source_language} to {target_language}: {text[:50]}...")
    
    # If source and target are the same, or target isn't supported, return original text
    if source_language == target_language or target_language not in LANGUAGE_NAMES:
        return text
    
    try:
        # In a real implementation, we would call a translation API here
        # For demo purposes, we'll simulate translation for common phrases
        
        # Check if this is a common phrase we have translations for
        if target_language in COMMON_PHRASES:
            for key, phrase in COMMON_PHRASES.get('en', {}).items():
                if phrase.lower() in text.lower():
                    translated_phrase = COMMON_PHRASES[target_language].get(key, phrase)
                    return text.lower().replace(phrase.lower(), translated_phrase)
        
        # For demo, add a prefix to show translation would happen
        return f"[Translated to {get_language_name(target_language)}] {text}"
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return text  # Return original text on error

def transliterate_text(text, source_language=None):
    """
    Transliterate text from non-Latin scripts to Latin
    This would be implemented with a proper transliteration API in a real app
    """
    logger.debug(f"Transliterating from {source_language}: {text[:50]}...")
    
    # Add simulated transliteration for demo purposes
    if source_language in ['ru', 'zh', 'ja', 'ko', 'ar']:
        return f"[Transliterated] {text}"
    
    return text

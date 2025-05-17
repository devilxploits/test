import os
import logging
import requests
import time
from datetime import datetime
import json
import random
from instagrapi import Client as InstagramClient
from telegram import Bot as TelegramBot
from telegram.error import TelegramError

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Initialize clients
instagram_client = None
telegram_bot = None

def init_instagram_client():
    """Initialize and authenticate Instagram client"""
    global instagram_client
    
    if not Config.INSTAGRAM_USERNAME or not Config.INSTAGRAM_PASSWORD:
        logger.warning("Instagram credentials not provided")
        return None
    
    try:
        client = InstagramClient()
        client.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
        instagram_client = client
        logger.info("Instagram client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Instagram client: {str(e)}")
        return None

def init_telegram_bot():
    """Initialize Telegram bot"""
    global telegram_bot
    
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram bot token not provided")
        return None
    
    try:
        bot = TelegramBot(Config.TELEGRAM_BOT_TOKEN)
        telegram_bot = bot
        logger.info("Telegram bot initialized successfully")
        return bot
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {str(e)}")
        return None

def publish_to_instagram(post):
    """Publish a content post to Instagram"""
    # Ensure client is initialized
    if not instagram_client:
        client = init_instagram_client()
        if not client:
            raise Exception("Instagram client initialization failed")
    
    try:
        # Format caption with hashtags
        caption = f"{post.caption}\n\n{post.hashtags}"
        
        # For demo purposes, we'll log the action rather than actually posting
        logger.info(f"Publishing to Instagram: {post.title}")
        logger.info(f"Caption: {caption}")
        logger.info(f"Image URL: {post.image_url}")
        
        # In a real implementation, we would download the image and then upload
        # image_path = download_image(post.image_url)
        # media = instagram_client.photo_upload(image_path, caption)
        # return media.pk
        
        # Return mock data for demo
        return f"instagram_post_{post.id}_{int(time.time())}"
    
    except Exception as e:
        logger.error(f"Error publishing to Instagram: {str(e)}")
        raise

def publish_to_telegram(post):
    """Publish a content post to Telegram"""
    # Ensure bot is initialized
    if not telegram_bot:
        bot = init_telegram_bot()
        if not bot:
            raise Exception("Telegram bot initialization failed")
    
    try:
        # Format caption with hashtags
        caption = f"{post.caption}\n\n{post.hashtags}"
        
        # For demo purposes, we'll log the action rather than actually posting
        logger.info(f"Publishing to Telegram: {post.title}")
        logger.info(f"Caption: {caption}")
        logger.info(f"Image URL: {post.image_url}")
        
        # In a real implementation, we would send to a channel or group
        # channel_id = Config.TELEGRAM_CHANNEL_ID
        # message = telegram_bot.send_photo(chat_id=channel_id, photo=post.image_url, caption=caption)
        # return message.message_id
        
        # Return mock data for demo
        return f"telegram_post_{post.id}_{int(time.time())}"
    
    except Exception as e:
        logger.error(f"Error publishing to Telegram: {str(e)}")
        raise

def get_instagram_comments(post_id=None, since_id=None, limit=20):
    """Get comments from Instagram posts"""
    # This would be implemented with the Instagram API in a real app
    # For demo purposes, return mock data
    
    mock_comments = [
        {"id": "123456", "username": "user1", "text": "You look amazing Sophia!", "timestamp": "2023-06-15T12:34:56"},
        {"id": "123457", "username": "user2", "text": "Love your content!", "timestamp": "2023-06-15T13:45:12"},
        {"id": "123458", "username": "user3", "text": "Can you share your skincare routine?", "timestamp": "2023-06-15T14:22:33"},
    ]
    
    return mock_comments

def get_telegram_messages(since_id=None, limit=20):
    """Get messages from Telegram"""
    # This would be implemented with the Telegram API in a real app
    # For demo purposes, return mock data
    
    mock_messages = [
        {"id": "234561", "username": "tg_user1", "text": "Hey Sophia, how are you today?", "timestamp": "2023-06-15T10:11:22"},
        {"id": "234562", "username": "tg_user2", "text": "Love your latest post!", "timestamp": "2023-06-15T11:33:44"},
        {"id": "234563", "username": "tg_user3", "text": "What's your favorite movie?", "timestamp": "2023-06-15T12:55:11"},
    ]
    
    return mock_messages

def reply_to_instagram_comment(comment_id, message):
    """Reply to an Instagram comment"""
    # This would be implemented with the Instagram API in a real app
    logger.info(f"Replying to Instagram comment {comment_id}: {message}")
    return True

def reply_to_telegram_message(chat_id, message):
    """Reply to a Telegram message"""
    # This would be implemented with the Telegram API in a real app
    logger.info(f"Replying to Telegram chat {chat_id}: {message}")
    return True

def publish_scheduled_posts():
    """
    Check for scheduled posts that need to be published and
    publish them to all specified platforms simultaneously
    
    Returns:
        list: List of results containing success/error information
    """
    from app import db
    from models import ContentPost
    
    # Get all scheduled posts that are due to be published
    now = datetime.now()
    scheduled_posts = ContentPost.query.filter(
        ContentPost.status == "scheduled",
        ContentPost.scheduled_for <= now
    ).all()
    
    if not scheduled_posts:
        logger.info("No posts scheduled for publishing at this time")
        return []
    
    results = []
    
    for post in scheduled_posts:
        post_result = {
            "post_id": post.id,
            "title": post.title,
            "platforms": []
        }
        
        # Parse platforms list
        try:
            platforms = post.platforms.split(",") if post.platforms else []
        except Exception as e:
            logger.error(f"Error parsing platforms for post {post.id}: {str(e)}")
            platforms = []
            post_result["error"] = f"Invalid platforms format: {str(e)}"
        
        # Track if any platform publishing succeeded
        any_success = False
        
        # Publish to each platform
        for platform in platforms:
            platform = platform.strip().lower()
            
            platform_result = {
                "platform": platform,
                "status": "attempted"
            }
            
            try:
                if platform == "instagram":
                    post_id = publish_to_instagram(post)
                    platform_result["status"] = "success"
                    platform_result["platform_post_id"] = post_id
                    any_success = True
                    
                elif platform == "telegram":
                    message_id = publish_to_telegram(post)
                    platform_result["status"] = "success"
                    platform_result["platform_post_id"] = message_id
                    any_success = True
                    
                else:
                    platform_result["status"] = "error"
                    platform_result["error"] = f"Unknown platform: {platform}"
                    
            except Exception as e:
                platform_result["status"] = "error"
                platform_result["error"] = str(e)
                logger.error(f"Error publishing to {platform}: {str(e)}")
            
            post_result["platforms"].append(platform_result)
        
        # Update post status based on publishing results
        if any_success:
            post.status = "published"
            post.published_at = now
        else:
            post.status = "failed"
            post.error_message = json.dumps(post_result)
        
        db.session.commit()
        results.append(post_result)
    
    return results

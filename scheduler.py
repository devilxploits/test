import logging
import threading
import time
import json
from datetime import datetime, timedelta
import random

from app import app, db
from models import ContentPost, SophiaSettings
from content_generator import generate_content, get_stock_photo
from social_media import publish_to_instagram, publish_to_telegram, publish_scheduled_posts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentScheduler:
    def __init__(self):
        self.check_interval = 60  # Check every minute
        self.is_running = False
        self.stop_event = threading.Event()
        self.last_auto_generation = None

    def check_scheduled_posts(self):
        """Check for scheduled posts that need to be published"""
        with app.app_context():
            # Use the improved function from social_media.py that handles concurrent posting
            results = publish_scheduled_posts()
            
            if results:
                succeeded = sum(1 for r in results if 'error' not in r)
                failed = len(results) - succeeded
                logger.info(f"Published {succeeded} posts successfully, {failed} failed")

    def generate_content_if_needed(self):
        """Generate new content based on settings"""
        with app.app_context():
            settings = SophiaSettings.query.first()
            
            if not settings:
                logger.warning("Settings not found, using defaults")
                # Use default post frequency of 1 per day
                post_frequency = 1
                images_per_day = 1
                reels_per_day = 0
                post_time_start = 9  # 9 AM
                post_time_end = 21   # 9 PM
                post_days = [0, 1, 2, 3, 4, 5, 6]  # All days of week
                auto_schedule = True
            else:
                post_frequency = getattr(settings, 'post_frequency', 1)
                images_per_day = getattr(settings, 'images_per_day', 1)
                reels_per_day = getattr(settings, 'reels_per_day', 0)
                post_time_start = getattr(settings, 'post_time_start', 9)
                post_time_end = getattr(settings, 'post_time_end', 21)
                
                # Handle post days as either string or list
                post_days_value = getattr(settings, 'post_days', '0,1,2,3,4,5,6')
                if isinstance(post_days_value, list):
                    post_days = post_days_value
                else:
                    post_days = [int(day) for day in post_days_value.split(',') if day.strip()]
                
                auto_schedule = getattr(settings, 'auto_schedule', True)
            
            # Skip if auto scheduling is disabled or post frequency is 0
            if not auto_schedule or post_frequency <= 0:
                logger.info("Auto scheduling is disabled or post frequency is 0")
                return
            
            # Check if today is an active day
            now = datetime.utcnow()
            today_weekday = now.weekday()
            if today_weekday not in post_days:
                logger.info(f"Today (weekday {today_weekday}) is not an active posting day")
                return
            
            # Calculate posts per type based on settings
            total_posts_needed = images_per_day + reels_per_day
            
            # If no posts needed, exit
            if total_posts_needed <= 0:
                logger.info("No posts needed based on current settings")
                return
                
            # Get number of posts already scheduled for today
            today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
            today_end = today_start + timedelta(days=1)
            
            # Count scheduled posts by type for today
            scheduled_images = ContentPost.query.filter(
                ContentPost.scheduled_for.between(today_start, today_end),
                ContentPost.status == 'scheduled',
                ContentPost.content_type == 'image'
            ).count()
            
            scheduled_reels = ContentPost.query.filter(
                ContentPost.scheduled_for.between(today_start, today_end),
                ContentPost.status == 'scheduled',
                ContentPost.content_type == 'reel'
            ).count()
            
            # Calculate how many more to create
            images_needed = max(0, images_per_day - scheduled_images)
            reels_needed = max(0, reels_per_day - scheduled_reels)
            
            logger.info(f"Content needed today: {images_needed} images, {reels_needed} reels")
            
            # If no more posts needed, exit
            if images_needed + reels_needed <= 0:
                return
                
            # Now create the needed content and schedule it
            # Calculate appropriate timing within allowed hours
            available_hours = list(range(post_time_start, post_time_end))
            
            if not available_hours:
                logger.warning("No available hours for posting based on settings")
                return
            
            # Calculate how many posts we need to create and schedule
            total_to_create = images_needed + reels_needed
            
            if total_to_create <= 0:
                return
                
            # Distribute posts throughout the available time slots
            current_hour = now.hour
            future_hours = [h for h in available_hours if h > current_hour]
            
            # If no future hours available today, exit - we'll create content tomorrow
            if not future_hours and current_hour >= post_time_end:
                logger.info("No more posting hours available today")
                return
                
            # Determine the spacing between posts
            if len(future_hours) >= total_to_create:
                # We have enough hours to space them out
                posting_hours = sorted(random.sample(future_hours, total_to_create))
            else:
                # Not enough hours, so we'll use all available hours
                posting_hours = future_hours
                
                # If we need more slots than available hours, we'll post multiple times in some hours
                if total_to_create > len(posting_hours) and posting_hours:
                    # Calculate how many additional slots we need
                    additional_needed = total_to_create - len(posting_hours)
                    
                    # Add additional slots by repeating some hours
                    extra_hours = random.choices(posting_hours, k=additional_needed)
                    posting_hours.extend(extra_hours)
                    posting_hours.sort()
            
            # Now create and schedule the content for each time slot
            posts_created = 0
            
            # First schedule images
            for _ in range(images_needed):
                if not posting_hours:
                    break
                    
                post_hour = posting_hours.pop(0)
                scheduled_time = datetime(now.year, now.month, now.day, post_hour, 
                                         random.randint(0, 59))  # Random minute
                
                # Create content for image post
                content = generate_content(content_style="lifestyle")
                
                # Create ContentPost object
                post = ContentPost(
                    title=content.get('title', 'Sophia AI Post'),
                    caption=content.get('caption', 'Check out my latest post!'),
                    content_type='image',
                    status='scheduled',
                    scheduled_for=scheduled_time,
                    published_at=None,
                    platforms='instagram,telegram',  # Post to both platforms
                    hashtags=content.get('hashtags', '#sophiaAI'),
                    media_path=content.get('image_url', get_stock_photo())
                )
                
                # Save to database
                db.session.add(post)
                posts_created += 1
                
            # Then schedule reels/videos
            for _ in range(reels_needed):
                if not posting_hours:
                    break
                    
                post_hour = posting_hours.pop(0)
                scheduled_time = datetime(now.year, now.month, now.day, post_hour, 
                                         random.randint(0, 59))  # Random minute
                
                # Create content for reel post
                content = generate_content(content_style="glamour")
                
                # Create ContentPost object
                post = ContentPost(
                    title=content.get('title', 'Sophia AI Reel'),
                    caption=content.get('caption', 'Check out my latest reel!'),
                    content_type='reel',
                    status='scheduled',
                    scheduled_for=scheduled_time,
                    published_at=None,
                    platforms='instagram,telegram',  # Post to both platforms
                    hashtags=content.get('hashtags', '#sophiaAI #reel'),
                    media_path=content.get('image_url', get_stock_photo())
                )
                
                # Save to database
                db.session.add(post)
                posts_created += 1
                
            # Commit all changes to the database
            if posts_created > 0:
                db.session.commit()
                logger.info(f"Created and scheduled {posts_created} posts for today")
                
            # Update the last auto generation timestamp
            self.last_auto_generation = now

    def run(self):
        """Run the scheduler loop"""
        self.is_running = True
        logger.info("Content scheduler is running")
        
        while not self.stop_event.is_set():
            try:
                # Check for scheduled posts that need to be published
                self.check_scheduled_posts()
                
                # Generate new content if needed
                self.generate_content_if_needed()
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
            
            # Sleep for the check interval
            self.stop_event.wait(self.check_interval)
        
        self.is_running = False
        logger.info("Content scheduler stopped")

    def start(self):
        """Start the scheduler in a separate thread"""
        if not self.is_running:
            thread = threading.Thread(target=self.run)
            thread.daemon = True
            thread.start()
            logger.info("Content scheduler started in background thread")
        else:
            logger.warning("Content scheduler already running")

    def stop(self):
        """Stop the scheduler"""
        self.stop_event.set()
        logger.info("Content scheduler stopping...")

def start_scheduler():
    """Start the content scheduler"""
    scheduler = ContentScheduler()
    scheduler.start()
    return scheduler
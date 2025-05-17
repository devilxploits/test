import logging
import os
import json
import shutil
from flask import render_template, redirect, url_for, request, flash, jsonify, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_socketio import emit
from langdetect import detect
from datetime import datetime, timedelta

from app import app, db, socketio
from models import User, Conversation, Message, ContentPost, SophiaSettings
from ai_service import generate_text_response, analyze_user_message
from content_generator import generate_content, generate_image
from social_media import publish_to_instagram, publish_to_telegram
from language_processor import translate_text, detect_language
from tts_service import generate_speech, get_available_voices
from paypal import load_paypal_default, create_paypal_order, capture_paypal_order

# Configure logging
logger = logging.getLogger(__name__)

# Helper functions
def get_or_create_settings():
    settings = SophiaSettings.query.first()
    if not settings:
        settings = SophiaSettings()
        db.session.add(settings)
        db.session.commit()
    return settings

def get_or_create_conversation(user_id=None, source="website", external_id=None):
    # For logged in users
    if user_id:
        conversation = Conversation.query.filter_by(user_id=user_id, source=source).first()
        if not conversation:
            conversation = Conversation(user_id=user_id, source=source)
            db.session.add(conversation)
            db.session.commit()
        return conversation
    
    # For anonymous users
    if external_id:
        conversation = Conversation.query.filter_by(external_id=external_id, source=source).first()
        if not conversation:
            conversation = Conversation(external_id=external_id, source=source)
            db.session.add(conversation)
            db.session.commit()
        return conversation
    
    # Use session ID for web anonymous users
    if not session.get('conversation_id'):
        conversation = Conversation(source=source)
        db.session.add(conversation)
        db.session.commit()
        session['conversation_id'] = conversation.id
        return conversation
    else:
        conversation = Conversation.query.get(session['conversation_id'])
        if not conversation:
            conversation = Conversation(source=source)
            db.session.add(conversation)
            db.session.commit()
            session['conversation_id'] = conversation.id
        return conversation

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/subscription')
def subscription():
    """Subscription page for premium features"""
    settings = get_or_create_settings()
    
    # Check if user is already a paid user
    if current_user.is_authenticated and current_user.is_paid:
        return render_template('subscription.html', already_subscribed=True)
    
    # Get subscription fee from settings
    subscription_fee = settings.subscription_fee
    
    return render_template('subscription.html', 
                          subscription_fee=subscription_fee,
                          already_subscribed=False)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('You do not have admin privileges')
        return redirect(url_for('index'))
    
    # Fetch data for admin dashboard
    conversations = Conversation.query.order_by(Conversation.last_interaction.desc()).limit(10).all()
    posts = ContentPost.query.order_by(ContentPost.created_at.desc()).limit(10).all()
    settings = get_or_create_settings()
    
    # Stats
    total_users = User.query.count()
    total_conversations = Conversation.query.count()
    total_messages = Message.query.count()
    total_posts = ContentPost.query.count()
    
    # Recent activity
    recent_messages = Message.query.order_by(Message.timestamp.desc()).limit(20).all()
    
    return render_template('admin.html', 
                          conversations=conversations, 
                          posts=posts, 
                          settings=settings,
                          total_users=total_users,
                          total_conversations=total_conversations,
                          total_messages=total_messages,
                          total_posts=total_posts,
                          recent_messages=recent_messages)

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def api_settings():
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    settings = get_or_create_settings()
    
    if request.method == 'POST':
        data = request.json
        
        # Update settings from form data
        if 'personality' in data:
            settings.personality = data['personality']
        if 'content_style' in data:
            settings.content_style = data['content_style']
        if 'response_length' in data:
            settings.response_length = int(data['response_length'])
        if 'flirt_level' in data:
            settings.flirt_level = int(data['flirt_level'])
        # Social media posting schedule settings
        if 'post_frequency' in data:
            settings.post_frequency = int(data['post_frequency'])
        if 'images_per_day' in data:
            settings.images_per_day = int(data['images_per_day'])
        if 'reels_per_day' in data:
            settings.reels_per_day = int(data['reels_per_day'])
        if 'post_time_start' in data:
            settings.post_time_start = int(data['post_time_start'])
        if 'post_time_end' in data:
            settings.post_time_end = int(data['post_time_end'])
        if 'post_days' in data:
            settings.post_days = data['post_days']
            
        # Instagram settings
        if 'instagram_settings' in data:
            settings.set_instagram_settings(data['instagram_settings'])
            
        # Telegram settings
        if 'telegram_settings' in data:
            settings.set_telegram_settings(data['telegram_settings'])
        
        # PayPal settings
        if 'paypal_settings' in data:
            settings.set_paypal_settings(data['paypal_settings'])
        
        # Subscription fee
        if 'subscription_fee' in data:
            settings.subscription_fee = float(data['subscription_fee'])
            
        # Kobold Horde API settings
        if 'kobold_model' in data:
            settings.kobold_model = data['kobold_model']
        if 'allow_nsfw' in data:
            settings.allow_nsfw = bool(data['allow_nsfw'])
        if 'kobold_api_key' in data and data['kobold_api_key'].strip():
            # Update the environment variable
            os.environ['KOBOLD_HORDE_API_KEY'] = data['kobold_api_key']
            # Also update the config
            app.config['KOBOLD_HORDE_API_KEY'] = data['kobold_api_key']
            
        # Piper TTS settings
        if 'use_tts' in data:
            settings.use_tts = bool(data['use_tts'])
        if 'tts_voice_id' in data:
            settings.tts_voice_id = data['tts_voice_id']
        if 'tts_speed' in data:
            settings.tts_speed = float(data['tts_speed'])
        if 'piper_api_key' in data and data['piper_api_key'].strip():
            # Update the environment variable
            os.environ['PIPER_TTS_API_KEY'] = data['piper_api_key']
            # Also update the config
            app.config['PIPER_TTS_API_KEY'] = data['piper_api_key']
            
        # PayPal API credentials
        if 'paypal_client_id' in data and data['paypal_client_id'].strip():
            # Update PayPal settings with client ID
            paypal_settings = settings.get_paypal_settings()
            paypal_settings['client_id'] = data['paypal_client_id']
            settings.set_paypal_settings(paypal_settings)
            
            # Also update environment variables
            os.environ['PAYPAL_CLIENT_ID'] = data['paypal_client_id']
            app.config['PAYPAL_CLIENT_ID'] = data['paypal_client_id']
            
        if 'paypal_client_secret' in data and data['paypal_client_secret'].strip():
            # Update PayPal settings with client secret
            paypal_settings = settings.get_paypal_settings()
            paypal_settings['client_secret'] = data['paypal_client_secret']
            settings.set_paypal_settings(paypal_settings)
            
            # Also update environment variables
            os.environ['PAYPAL_CLIENT_SECRET'] = data['paypal_client_secret']
            app.config['PAYPAL_CLIENT_SECRET'] = data['paypal_client_secret']
        
        if 'paypal_environment' in data:
            # Update PayPal environment (sandbox/production)
            paypal_settings = settings.get_paypal_settings()
            paypal_settings['environment'] = data['paypal_environment']
            settings.set_paypal_settings(paypal_settings)
            
        if 'paypal_business_email' in data:
            # Update PayPal business email
            paypal_settings = settings.get_paypal_settings()
            paypal_settings['business_email'] = data['paypal_business_email']
            settings.set_paypal_settings(paypal_settings)
        
        db.session.commit()
        return jsonify({"success": True})
    
    return jsonify({
        "personality": settings.personality,
        "content_style": settings.content_style,
        "response_length": settings.response_length,
        "flirt_level": settings.flirt_level,
        "post_frequency": settings.post_frequency,
        "images_per_day": settings.images_per_day,
        "reels_per_day": settings.reels_per_day,
        "post_time_start": settings.post_time_start,
        "post_time_end": settings.post_time_end,
        "post_days": settings.post_days,
        "subscription_fee": settings.subscription_fee,
        "instagram_settings": settings.get_instagram_settings(),
        "telegram_settings": settings.get_telegram_settings(),
        "paypal_settings": settings.get_paypal_settings()
    })

@app.route('/api/generate_image', methods=['POST'])
@login_required
def api_generate_image():
    """Endpoint for generating images with Stable Diffusion"""
    # Check if user can generate images
    if not current_user.is_admin and not current_user.is_paid:
        return jsonify({"error": "This feature is only available for paid users"}), 403
        
    # Check daily limits for paid users
    if not current_user.is_admin and not current_user.can_generate_image():
        return jsonify({"error": "You have reached your daily limit of 2 generated images"}), 429
    
    # Get prompt from request
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "Image prompt is required"}), 400
        
    try:
        # Generate image with Stable Diffusion
        image_url = generate_image(prompt)
        
        if not image_url:
            return jsonify({"error": "Failed to generate image"}), 500
            
        # Decrement the user's daily quota if not admin
        if not current_user.is_admin:
            current_user.daily_image_limit -= 1
            db.session.commit()
            
        return jsonify({
            "success": True, 
            "image_url": image_url,
            "remaining_quota": current_user.daily_image_limit if not current_user.is_admin else "unlimited"
        })
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/voice_call', methods=['POST'])
@login_required
def api_voice_call():
    """Endpoint for generating voice responses"""
    # Check if user can make voice calls
    if not current_user.is_admin and not current_user.is_paid:
        return jsonify({"error": "This feature is only available for paid users"}), 403
        
    # Estimate call duration
    data = request.json
    text = data.get('text', '')
    duration_minutes = max(1, len(text) // 200)  # Rough estimate: 200 chars ≈ 1 minute
    
    # Check daily limits for paid users
    if not current_user.is_admin and not current_user.can_make_call(duration_minutes):
        return jsonify({"error": f"You have reached your daily limit of 10 minutes for voice calls"}), 429
    
    if not text:
        return jsonify({"error": "Text content is required"}), 400
        
    try:
        # Generate voice with TTS service
        voice_id = data.get('voice_id', 'female_sensual')
        audio_path = generate_speech(text, voice_id)
        
        if not audio_path:
            return jsonify({"error": "Failed to generate voice response"}), 500
            
        # Decrement the user's daily quota if not admin
        if not current_user.is_admin:
            current_user.daily_call_minutes -= duration_minutes
            db.session.commit()
            
        return jsonify({
            "success": True, 
            "audio_url": audio_path,
            "duration_minutes": duration_minutes,
            "remaining_minutes": current_user.daily_call_minutes if not current_user.is_admin else "unlimited"
        })
        
    except Exception as e:
        logger.error(f"Error generating voice: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/content', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_content():
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    if request.method == 'GET':
        # Get list of posts with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        posts = ContentPost.query.order_by(ContentPost.created_at.desc()).paginate(page=page, per_page=per_page)
        
        posts_list = []
        for post in posts.items:
            posts_list.append({
                "id": post.id,
                "title": post.title,
                "caption": post.caption[:100] + "..." if len(post.caption) > 100 else post.caption,
                "status": post.status,
                "created_at": post.created_at.strftime('%Y-%m-%d %H:%M'),
                "scheduled_for": post.scheduled_for.strftime('%Y-%m-%d %H:%M') if post.scheduled_for else None,
                "published_at": post.published_at.strftime('%Y-%m-%d %H:%M') if post.published_at else None
            })
            
        return jsonify({
            "posts": posts_list,
            "total": posts.total,
            "pages": posts.pages,
            "current_page": posts.page
        })
    
    elif request.method == 'POST':
        data = request.json
        
        if 'generate' in data and data['generate']:
            # Auto-generate content
            theme = data.get('theme', '')
            style = data.get('style', '')
            platforms = data.get('platforms', ['instagram', 'telegram'])
            
            settings = get_or_create_settings()
            
            try:
                # Generate content using AI
                content = generate_content(theme, style, settings.content_style, settings.personality)
                
                # Create new post with content type
                post = ContentPost()
                post.title = content['title']
                post.caption = content['caption']
                post.hashtags = content['hashtags']
                post.image_prompt = content['image_prompt']
                post.status = "draft"
                
                # Set content type (default to image)
                content_type = data.get('content_type', 'image')
                if content_type in ['image', 'video', 'reel']:
                    post.content_type = content_type
                else:
                    post.content_type = 'image'
                
                # Set platforms as comma-separated string
                if isinstance(platforms, list):
                    post.platforms = ','.join(platforms)
                else:
                    post.platforms = platforms
                
                # If scheduling is requested
                if 'schedule_for' in data and data['schedule_for']:
                    scheduled_time = datetime.fromisoformat(data['schedule_for'])
                    post.scheduled_for = scheduled_time
                    post.status = "scheduled"
                
                db.session.add(post)
                db.session.commit()
                
                # Generate image asynchronously (in a real implementation, this would be a background task)
                image_url = generate_image(post.image_prompt)
                post.image_url = image_url
                db.session.commit()
                
                return jsonify({
                    "success": True,
                    "post_id": post.id,
                    "message": "Content created successfully"
                })
                
            except Exception as e:
                logger.error(f"Error generating content: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        # Manual content creation
        if 'id' in data:  # Edit existing post
            post = ContentPost.query.get(data['id'])
            if not post:
                return jsonify({"error": "Post not found"}), 404
        else:  # Create new post
            post = ContentPost()
            post.status = "draft"
        
        # Update post data
        post.title = data.get('title', post.title)
        post.caption = data.get('caption', post.caption)
        post.hashtags = data.get('hashtags', post.hashtags)
        
        if 'image_prompt' in data:
            post.image_prompt = data['image_prompt']
            # Generate image based on prompt (in real implementation this would be async)
            try:
                image_url = generate_image(post.image_prompt)
                post.image_url = image_url
            except Exception as e:
                logger.error(f"Error generating image: {str(e)}")
                return jsonify({"error": f"Error generating image: {str(e)}"}), 500
                
        if 'platforms' in data:
            post.set_platforms(data['platforms'])
            
        if 'schedule_for' in data and data['schedule_for']:
            scheduled_time = datetime.fromisoformat(data['schedule_for'])
            post.scheduled_for = scheduled_time
            post.status = "scheduled"
        
        if 'publish_now' in data and data['publish_now']:
            try:
                # Publish to selected platforms
                for platform in post.get_platforms():
                    if platform == 'instagram':
                        publish_to_instagram(post)
                    elif platform == 'telegram':
                        publish_to_telegram(post)
                
                post.status = "published"
                post.published_at = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error publishing post: {str(e)}")
                post.status = "failed"
                post.error_message = str(e)
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "post_id": post.id
        })
    
    elif request.method == 'DELETE':
        post_id = request.args.get('id')
        if not post_id:
            return jsonify({"error": "Post ID required"}), 400
            
        post = ContentPost.query.get(post_id)
        if not post:
            return jsonify({"error": "Post not found"}), 404
            
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({"success": True})

@app.route('/api/chat_history')
def api_chat_history():
    conversation = None
    
    # Get the appropriate conversation
    if current_user.is_authenticated:
        conversation = get_or_create_conversation(user_id=current_user.id)
    else:
        conversation = get_or_create_conversation()
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    # Get messages with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    messages = Message.query.filter_by(conversation_id=conversation.id)\
        .order_by(Message.timestamp.desc())\
        .paginate(page=page, per_page=per_page)
    
    # Format messages for the client
    message_list = []
    for msg in reversed(messages.items):  # Reverse to get chronological order
        message_list.append({
            "id": msg.id,
            "content": msg.content,
            "is_from_user": msg.is_from_user,
            "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        "conversation_id": conversation.id,
        "messages": message_list,
        "total": messages.total,
        "pages": messages.pages,
        "current_page": messages.page
    })

# Socket.IO chat handling
@socketio.on('connect')
def socket_connect():
    logger.debug("Client connected to Socket.IO")

@socketio.on('disconnect')
def socket_disconnect():
    logger.debug("Client disconnected from Socket.IO")

@socketio.on('message')
def handle_message(data):
    logger.debug(f"Received message: {data}")
    
    # Get user message
    user_message = data.get('message', '')
    if not user_message.strip():
        emit('response', {'error': 'Empty message'})
        return
    
    try:
        # Get the appropriate conversation
        if current_user.is_authenticated:
            conversation = get_or_create_conversation(user_id=current_user.id)
        else:
            conversation = get_or_create_conversation()
        
        # Detect language
        try:
            detected_lang = detect_language(user_message)
            if detected_lang != conversation.detected_language:
                conversation.detected_language = detected_lang
                db.session.commit()
        except:
            # If language detection fails, use English as fallback
            detected_lang = 'en'
        
        # Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            content=user_message,
            is_from_user=True
        )
        db.session.add(user_msg)
        
        # Update conversation last interaction time
        conversation.last_interaction = datetime.utcnow()
        db.session.commit()
        
        # Analyze the message intent and sentiment
        analysis = analyze_user_message(user_message)
        
        # Generate AI response
        settings = get_or_create_settings()
        ai_response = generate_text_response(
            user_message, 
            conversation_id=conversation.id,
            flirt_level=settings.flirt_level,
            language=detected_lang,
            model_name=settings.kobold_model,
            nsfw=settings.allow_nsfw
        )
        
        # Save AI response
        ai_msg = Message(
            conversation_id=conversation.id,
            content=ai_response,
            is_from_user=False
        )
        db.session.add(ai_msg)
        db.session.commit()
        
        # Send the response back to the client
        emit('response', {
            'message': ai_response,
            'message_id': ai_msg.id,
            'timestamp': ai_msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        emit('response', {'error': 'Sorry, I encountered an error processing your message.'})

# TTS API endpoint
@app.route('/api/tts', methods=['POST'])
def api_tts():
    """
    API endpoint to generate speech from text using Piper TTS
    
    Expected JSON parameters:
    - text: The text to convert to speech
    - voice: The voice ID to use (default: female_casual)
    - provider: The TTS provider ('piper' or 'browser')
    """
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
            
        data = request.json
        text = data.get('text', '')
        voice = data.get('voice', 'female_casual')
        provider = data.get('provider', 'piper')
        
        if not text:
            return jsonify({"success": False, "error": "Missing required field: text"}), 400
            
        # Get settings to check if TTS is enabled
        settings = get_or_create_settings()
        
        # If provider is piper, use Piper TTS
        if provider == 'piper':
            # Check if Piper TTS is enabled in settings
            if not settings.use_tts:
                return jsonify({"success": False, "error": "TTS is disabled in settings"}), 400
                
            try:
                # Generate speech using Piper TTS
                audio_file_path = generate_speech(
                    text=text,
                    voice_id=voice,
                    speed=settings.tts_speed
                )
                
                if not audio_file_path:
                    logger.error("Failed to generate TTS audio")
                    return jsonify({"success": False, "error": "Failed to generate audio"}), 500
            except ValueError as ve:
                # Handle missing API key error
                error_msg = str(ve)
                logger.warning(f"TTS API error: {error_msg}")
                return jsonify({"success": False, "error": error_msg}), 400
                
            # Create static/audio directory if it doesn't exist
            audio_dir = os.path.join('static', 'audio')
            os.makedirs(audio_dir, exist_ok=True)
            
            # Copy the file to the static folder for serving
            filename = os.path.basename(audio_file_path)
            static_path = os.path.join(audio_dir, filename)
            shutil.copy(audio_file_path, static_path)
            
            # Return the URL to the audio file
            audio_url = url_for('static', filename=f'audio/{filename}')
            
            return jsonify({
                "success": True, 
                "audio_url": audio_url,
                "voice": voice,
                "provider": "piper"
            })
            
        # Otherwise, use browser-based TTS (no processing required on server)
        return jsonify({
            "success": True,
            "audio_url": None,
            "provider": "browser"
        })
            
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# PayPal API Endpoints

@app.route('/paypal/setup', methods=['GET'])
def paypal_setup():
    """Get PayPal configuration for the client side"""
    # Pass Flask request/response objects to the PayPal module
    return load_paypal_default(request, jsonify)

@app.route('/paypal/order', methods=['POST'])
def paypal_create_order():
    """Create a PayPal order for subscription payment"""
    # Pass Flask request/response objects to the PayPal module
    return create_paypal_order(request, jsonify)

@app.route('/paypal/order/<order_id>/capture', methods=['POST'])
def paypal_capture_order(order_id):
    """Capture payment for a PayPal order"""
    # Add order_id to request params for the PayPal module
    request.params = {'orderID': order_id}
    
    # Set current user info on request for the PayPal module
    if current_user.is_authenticated:
        request.user = current_user
    
    # Pass Flask request/response objects to the PayPal module
    return capture_paypal_order(request, jsonify)

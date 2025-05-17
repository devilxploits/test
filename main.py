from app import app  # noqa: F401
from flask import render_template, redirect, url_for, request, flash, jsonify, session
from datetime import timedelta
from flask_login import current_user

# Import PayPal functions
from paypal import load_paypal_default, create_paypal_order, capture_paypal_order
# Import database models
from models import SophiaSettings
# Import scheduler
from scheduler import start_scheduler

# Configure session lifetime for "Remember Me" feature
app.permanent_session_lifetime = timedelta(days=30)  # Session lasts for 30 days if permanent

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Chat route
@app.route('/chat')
def chat():
    return render_template('chat.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Very simple login for now - case insensitive username
        if username and password and username.lower() == 'admin'.lower() and password == 'admin123':
            # Check if the "Remember Me" option is selected
            remember = True if request.form.get('remember') else False
            # In a real app, we would use Flask-Login here to persist the session
            session.permanent = remember  # This will make the session last longer if remember is True
            flash('Login successful')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

# Admin route 
@app.route('/admin')
def admin():
    return render_template('admin.html')

# Subscription route
@app.route('/subscription')
def subscription():
    """Subscription page for premium features"""
    # Get settings
    settings = SophiaSettings.query.first()
    if not settings:
        settings = SophiaSettings()
        from app import db
        db.session.add(settings)
        db.session.commit()
    
    # Check if user is already a paid user
    is_paid = False
    if current_user.is_authenticated and hasattr(current_user, 'is_paid'):
        is_paid = current_user.is_paid
    
    # Get subscription fee from settings
    subscription_fee = settings.subscription_fee
    
    return render_template('subscription.html', 
                          subscription_fee=subscription_fee,
                          already_subscribed=is_paid)

# API Route for settings
@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """API endpoint for getting and saving settings"""
    from app import db
    
    # Get settings
    settings = SophiaSettings.query.first()
    if not settings:
        settings = SophiaSettings()
        db.session.add(settings)
        db.session.commit()
    
    # Handle POST request to update settings
    if request.method == 'POST':
        data = request.json
        
        # Update PayPal settings
        if 'paypal_client_id' in data:
            settings.set_paypal_settings({
                'client_id': data.get('paypal_client_id', ''),
                'client_secret': data.get('paypal_client_secret', ''),
                'environment': data.get('paypal_environment', 'sandbox'),
                'business_email': data.get('paypal_business_email', '')
            })
        
        # Update subscription fee
        if 'subscription_fee' in data:
            try:
                settings.subscription_fee = float(data.get('subscription_fee', 9.99))
            except ValueError:
                return jsonify({'error': 'Invalid subscription fee'}), 400
        
        # Save changes
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Settings saved successfully'})
    
    # Handle GET request to retrieve settings
    else:
        # Get PayPal settings
        paypal_settings = settings.get_paypal_settings()
        
        # Format response with necessary settings
        response = {
            'subscription_fee': settings.subscription_fee,
            'paypal_client_id': paypal_settings.get('client_id', ''),
            'paypal_client_secret': paypal_settings.get('client_secret', ''),
            'paypal_environment': paypal_settings.get('environment', 'sandbox'),
            'paypal_business_email': paypal_settings.get('business_email', '')
        }
        
        return jsonify(response)

# PayPal routes
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
    # We need to add custom attributes as the PayPal module expects them
    setattr(request, 'params', {'orderID': order_id})
    
    # Set current user info on request for the PayPal module
    if current_user.is_authenticated:
        setattr(request, 'user', current_user)
    
    # Pass Flask request/response objects to the PayPal module
    return capture_paypal_order(request, jsonify)

if __name__ == "__main__":
    # Start the content scheduler
    start_scheduler()
    print("Content scheduler started")
    
    # Start the Flask server on port 5000, accessible externally
    app.run(host="0.0.0.0", port=5000, debug=True)

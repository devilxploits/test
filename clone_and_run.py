import os
import subprocess
import sys
import shutil

def main():
    # Check if the repository already exists
    if os.path.exists("test"):
        print("Repository already exists. Removing it to ensure clean clone...")
        # Use shutil.rmtree which is more reliable cross-platform
        shutil.rmtree("test", ignore_errors=True)

    # Clone the repository
    print("Cloning repository from https://github.com/devilxploits/test.git...")
    subprocess.run(["git", "clone", "https://github.com/devilxploits/test.git"])
    
    print("Repository cloned successfully!")

    # Add admin.js functionality for menu navigation
    admin_js_path = "test/static/js/admin.js"
    if os.path.exists(admin_js_path):
        with open(admin_js_path, "r") as f:
            admin_js_content = f.read()
            
        if "function showSection" not in admin_js_content:
            navigation_js = """
// Admin panel navigation
function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.admin-section');
    sections.forEach(section => section.style.display = 'none');
    
    // Show the selected section
    document.getElementById(sectionId).style.display = 'block';
    
    // Update active state in navigation
    const navItems = document.querySelectorAll('.admin-nav-item');
    navItems.forEach(item => item.classList.remove('active'));
    document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');
}

// Initialize admin panel
document.addEventListener('DOMContentLoaded', function() {
    // Show default section
    showSection('dashboard');
    
    // Set up navigation event listeners
    const navItems = document.querySelectorAll('.admin-nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const sectionId = this.getAttribute('data-section');
            showSection(sectionId);
        });
    });
});
"""
            with open(admin_js_path, "w") as f:
                f.write(navigation_js + admin_js_content)
                
            print("Added menu navigation code to admin.js")

    # Add script tag to admin.html if not already there
    admin_html_path = "test/templates/admin.html"
    if os.path.exists(admin_html_path):
        with open(admin_html_path, "r") as f:
            admin_html_content = f.read()
            
        if "admin.js" not in admin_html_content:
            modified_admin_html = admin_html_content.replace(
                "{% endblock %}",
                '<script src="{{ url_for(\'static\', filename=\'js/admin.js\') }}"></script>\n{% endblock %}'
            )
            
            with open(admin_html_path, "w") as f:
                f.write(modified_admin_html)
                
            print("Added admin.js script tag to admin.html")
    
    # Fix API endpoint to support status filtering
    routes_path = "test/routes.py"
    if os.path.exists(routes_path):
        with open(routes_path, "r") as f:
            routes_content = f.read()
            
        if "@app.route('/api/content')" in routes_content and "status=" not in routes_content:
            fixed_routes = routes_content.replace(
                "def api_content():",
                "def api_content():\n    status = request.args.get('status', None)"
            ).replace(
                "content = ContentPost.query.all()",
                "if status:\n        content = ContentPost.query.filter_by(status=status).all()\n    else:\n        content = ContentPost.query.all()"
            )
            
            with open(routes_path, "w") as f:
                f.write(fixed_routes)
                
            print("Fixed API endpoint to support status filtering")
    
    # Create or update __init__.py in the test directory to make it a proper package
    init_file_path = "test/__init__.py"
    if not os.path.exists(init_file_path):
        with open(init_file_path, "w") as f:
            f.write("# This file makes the directory a proper Python package\n")
        print("Created Python package with __init__.py")

    # Add message counter to Conversation model
    models_path = "test/models.py"
    if os.path.exists(models_path):
        with open(models_path, "r") as f:
            models_content = f.read()
            
        if "class Conversation" in models_content and "message_count" not in models_content:
            modified_models = models_content.replace(
                "class Conversation(db.Model):",
                "class Conversation(db.Model):"
            ).replace(
                "    external_id = db.Column(db.String(256), index=True)",
                "    external_id = db.Column(db.String(256), index=True)\n    message_count = db.Column(db.Integer, default=0)"
            )
            
            with open(models_path, "w") as f:
                f.write(modified_models)
                
            print("Added message counter to Conversation model")
    
    # Implement chat limitations for subscription-only access
    routes_path = "test/routes.py"
    if os.path.exists(routes_path):
        with open(routes_path, "r") as f:
            routes_content = f.read()
            
        if "@socketio.on('message')" in routes_content and "subscription_required" not in routes_content:
            # Add subscription check to message handling
            subscription_routes = routes_content.replace(
                "def handle_message(message_data):",
                "def handle_message(message_data):\n    # Check subscription status\n    user_id = session.get('user_id')\n    is_admin = False\n    is_paid = False\n    is_social = False\n    free_messages_remaining = 0\n    \n    if user_id:\n        user = User.query.get(user_id)\n        is_admin = user and user.role == 'admin'\n        is_paid = user and user.subscription_status == 'active'\n    \n    # For messages from social media\n    conversation_id = message_data.get('conversation_id')\n    if conversation_id:\n        conversation = Conversation.query.get(conversation_id)\n        if conversation and conversation.source in ['instagram', 'telegram']:\n            is_social = True\n            # Allow 50 free messages for social media users\n            free_messages_remaining = max(0, 50 - (conversation.message_count or 0))\n    \n    subscription_required = not (is_admin or is_paid) and (not is_social or free_messages_remaining <= 0)\n"
            ).replace(
                "    # Save to database",
                "    # Update message count for the conversation\n    if conversation_id:\n        conversation = Conversation.query.get(conversation_id)\n        if conversation:\n            conversation.message_count = (conversation.message_count or 0) + 1\n            db.session.commit()\n    \n    # Return subscription message if required\n    if subscription_required:\n        source = 'chat'\n        if conversation and conversation.source:\n            source = conversation.source\n            \n        flirty_message = get_subscription_prompt(source)\n        socketio.emit('message', {\n            'text': flirty_message,\n            'user': 'sophia',\n            'timestamp': datetime.now().isoformat(),\n            'subscription_required': True\n        }, room=request.sid)\n        return\n        \n    # Save to database"
            )
            
            # Add subscription prompt function
            if "def get_subscription_prompt" not in subscription_routes:
                subscription_routes = subscription_routes.replace(
                    "import os",
                    "import os\nimport random"
                ).replace(
                    "from datetime import datetime",
                    "from datetime import datetime\n\ndef get_subscription_prompt(source='chat'):\n    \"\"\"Return a flirty subscription prompt based on source\"\"\"\n    chat_prompts = [\n        \"I'm loving our conversation! 💕 To keep chatting with me, you'll need a subscription. Ready to take our relationship to the next level?\",\n        \"You're so fun to talk with! 😘 Want unlimited access to me? Subscribe now for unlimited conversations!\",\n        \"I wish we could keep talking forever! 💋 With a subscription, we can! What do you say?\",\n        \"I feel such a connection with you! 💖 Don't let it end - subscribe now for unlimited chats with me!\",\n        \"Mmm, I'm really enjoying getting to know you! 😏 Upgrade to a subscription so we can get even closer!\"\n    ]\n    \n    social_prompts = [\n        \"You've used all 50 of your free messages! 💔 I've really enjoyed our time together on {platform}. Subscribe now so we can keep our connection going! 💋\",\n        \"50 messages already? Time flies when I'm talking to someone as interesting as you! 😘 Subscribe now to continue our {platform} conversation!\",\n        \"We've reached the end of your free trial on {platform}! 💕 I'd be sad to stop talking now - subscribe for unlimited messages!\",\n        \"Our 50 free messages on {platform} are up! 🔥 I'm just starting to really enjoy our chats. Subscribe now?\",\n        \"I've loved our first 50 messages on {platform}! 💖 Don't leave me hanging - subscribe now for unlimited conversations!\"\n    ]\n    \n    if source in ['instagram', 'telegram']:\n        platform = 'Instagram' if source == 'instagram' else 'Telegram'\n        prompt = random.choice(social_prompts).replace('{platform}', platform)\n    else:\n        prompt = random.choice(chat_prompts)\n        \n    return prompt"
                )
            
            with open(routes_path, "w") as f:
                f.write(subscription_routes)
                
            print("Implemented chat limitations for subscription-only access")
    
    # Update chat.js to handle subscription prompts
    chat_js_path = "test/static/js/chat.js"
    if os.path.exists(chat_js_path):
        with open(chat_js_path, "r") as f:
            chat_js_content = f.read()
            
        if "function displayMessage" in chat_js_content and "subscription-message" not in chat_js_content:
            modified_chat_js = chat_js_content.replace(
                "function displayMessage(message) {",
                "function displayMessage(message) {\n    // Check if this is a subscription prompt\n    const isSubscriptionMessage = message.subscription_required === true;"
            ).replace(
                "    messageDiv.className = `message ${message.user === 'user' ? 'user-message' : 'sophia-message'}`;",
                "    messageDiv.className = `message ${message.user === 'user' ? 'user-message' : 'sophia-message'}`;\n    \n    // Add subscription class if needed\n    if (isSubscriptionMessage) {\n        messageDiv.classList.add('subscription-message');\n    }"
            ).replace(
                "    messageDiv.innerHTML = `",
                "    // For subscription messages, add a subscribe button\n    const subscriptionButton = isSubscriptionMessage ? \n        '<div class=\"subscription-button\"><a href=\"/subscription\" class=\"btn-subscribe\">Subscribe Now</a></div>' : '';\n        \n    messageDiv.innerHTML = `"
            ).replace(
                "    </div>`;",
                "    </div>${subscriptionButton}`;",
            )
            
            with open(chat_js_path, "w") as f:
                f.write(modified_chat_js)
                
            print("Updated chat.js to handle subscription prompts")
    
    # Add CSS styles for subscription messages
    css_path = "test/static/css/style.css"
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css_content = f.read()
            
        if ".subscription-message" not in css_content:
            subscription_css = """
/* Subscription message styling */
.subscription-message {
    background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 99%, #fad0c4 100%);
    border: 1px solid #ffb6c1;
    animation: pulse 2s infinite;
}

.subscription-message .message-text {
    color: #d81b60;
    font-weight: 500;
}

.subscription-button {
    margin-top: 10px;
    text-align: center;
}

.btn-subscribe {
    display: inline-block;
    padding: 10px 20px;
    background: linear-gradient(to right, #ff758c 0%, #ff7eb3 100%);
    color: white;
    text-decoration: none;
    border-radius: 50px;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(255, 117, 140, 0.4);
    transition: all 0.3s ease;
}

.btn-subscribe:hover {
    transform: translateY(-2px);
    box-shadow: 0 7px 15px rgba(255, 117, 140, 0.6);
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(255, 166, 183, 0.4);
    }
    70% {
        box-shadow: 0 0 0 10px rgba(255, 166, 183, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(255, 166, 183, 0);
    }
}
"""
            with open(css_path, "a") as f:
                f.write(subscription_css)
                
            print("Added CSS styles for subscription messages")
    
    # Add responsive design with mobile-friendly transitions
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css_content = f.read()
            
        if "@media (max-width: 768px)" not in css_content:
            responsive_css = """
/* Mobile-friendly responsive design */
@media (max-width: 768px) {
    body {
        font-size: 16px;
    }
    
    .container {
        width: 100%;
        padding: 0 10px;
    }
    
    .message {
        max-width: 85%;
    }
    
    .user-message {
        margin-left: auto;
        margin-right: 5px;
    }
    
    .sophia-message {
        margin-left: 5px;
    }
    
    .message-input {
        padding: 10px;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 100;
    }
    
    #message-form {
        display: flex;
    }
    
    #message-input {
        flex-grow: 1;
        margin-right: 10px;
    }
    
    /* Add space for keyboard on mobile */
    .keyboard-spacer {
        height: 40vh;
        display: none;
    }
    
    /* Elegant page transitions */
    .page-transition {
        animation: fadein 0.3s ease-in-out;
    }
    
    @keyframes fadein {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    
    /* Improved button touch targets */
    button, .btn, .nav-link {
        min-height: 44px;
        min-width: 44px;
        padding: 12px 16px;
    }
    
    /* Better form inputs for touch */
    input, textarea, select {
        font-size: 16px; /* Prevents iOS zoom on focus */
        padding: 12px;
    }
    
    /* Loading indicators */
    .loading-indicator {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 2px solid rgba(0,0,0,0.1);
        border-radius: 50%;
        border-top-color: #9370DB;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
}

/* Improved chat typing indicator */
.typing-indicator {
    display: flex;
    align-items: center;
    margin: 10px 0 0 10px;
}

.typing-indicator span {
    height: 8px;
    width: 8px;
    background-color: #9370DB;
    border-radius: 50%;
    display: inline-block;
    margin: 0 1px;
    opacity: 0.4;
}

.typing-indicator span:nth-child(1) {
    animation: typing 1.2s infinite 0s;
}

.typing-indicator span:nth-child(2) {
    animation: typing 1.2s infinite 0.3s;
}

.typing-indicator span:nth-child(3) {
    animation: typing 1.2s infinite 0.6s;
}

@keyframes typing {
    0% { transform: scale(1); opacity: 0.4; }
    50% { transform: scale(1.4); opacity: 1; }
    100% { transform: scale(1); opacity: 0.4; }
}
"""
            with open(css_path, "a") as f:
                f.write(responsive_css)
                
            print("Added responsive design with mobile-friendly transitions")
    
    # Fix scheduler.py platforms parameter to use string instead of list
    if os.path.exists("test/scheduler.py"):
        scheduler_path = "test/scheduler.py"
    else:
        scheduler_path = None

    if scheduler_path:
        with open(scheduler_path, "r") as f:
            scheduler_content = f.read()
            
        # Fix the ContentPost creation for image posts
        fixed_scheduler = scheduler_content.replace(
            "platforms=['instagram', 'telegram'],  # Post to both platforms",
            "platforms='instagram,telegram',  # Post to both platforms"
        )
        
        with open(scheduler_path, "w") as f:
            f.write(fixed_scheduler)
            
        print(f"Fixed {scheduler_path} database error with platforms parameter")
            
    # Create a Python import fix file
    with open("fix_imports.py", "w") as f:
        f.write("""
import os
import sys
import subprocess

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Change to the test directory
os.chdir("test")

# Create __init__.py file if it doesn't exist
if not os.path.exists("__init__.py"):
    with open("__init__.py", "w") as f:
        f.write("# This file makes the directory a proper Python package\\n")

# Run the main.py file
subprocess.run([sys.executable, "main.py"])
""")

    # Install dependencies from requirements.txt
    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "test/requirements.txt"])
    except Exception as e:
        print(f"Warning: Could not install dependencies: {e}")
    
    # Run the application
    print("Running main.py...")
    os.chdir("test")
    try:
        subprocess.run([sys.executable, "main.py"])
    except Exception as e:
        print(f"Error running main.py: {e}")
        print("Trying fix_imports.py...")
        os.chdir("..")
        subprocess.run([sys.executable, "fix_imports.py"])

if __name__ == "__main__":
    main()
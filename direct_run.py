#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

def main():
    # Delete the repository if it exists to ensure a clean start
    if os.path.exists("test"):
        print("Repository exists. Removing it to ensure clean clone...")
        shutil.rmtree("test", ignore_errors=True)

    # Clone the repository
    print("Cloning repository...")
    subprocess.run(["git", "clone", "https://github.com/devilxploits/test.git"])
    
    # Create a models.py file directly in the test directory 
    # This avoids import issues by keeping models.py in the same directory as app.py
    app_path = "test/app.py"
    models_path = "test/models.py"
    
    # First let's analyze the existing models.py file if it exists
    if os.path.exists(models_path):
        # Fix scheduler.py platforms parameter to use string instead of list
        scheduler_path = "test/scheduler.py"
        if os.path.exists(scheduler_path):
            with open(scheduler_path, "r") as f:
                scheduler_content = f.read()
                
            # Fix the ContentPost creation for image posts
            fixed_scheduler = scheduler_content.replace(
                "platforms=['instagram', 'telegram'],",
                "platforms='instagram,telegram',"
            )
            
            with open(scheduler_path, "w") as f:
                f.write(fixed_scheduler)
                
            print("Fixed scheduler.py database error with platforms parameter")
            
        # Add message counter to Conversation model
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
            
        # Add minimal subscription message styling without changing the overall design
        css_path = "test/static/css/style.css"
        if os.path.exists(css_path):
            with open(css_path, "r") as f:
                css_content = f.read()
                
            if ".subscription-message" not in css_content:
                # Add only the essential subscription message styling
                minimal_subscription_css = """
/* Subscription message styling */
.subscription-message {
    border: 1px solid #ffb6c1;
}

.subscription-button {
    margin-top: 10px;
    text-align: center;
}

.btn-subscribe {
    display: inline-block;
    padding: 8px 16px;
    background: #9370DB;
    color: white;
    text-decoration: none;
    border-radius: 4px;
}
"""
                with open(css_path, "a") as f:
                    f.write(minimal_subscription_css)
                    
                print("Added minimal subscription message styling")
    
    # Fix the import issue in app.py by directly editing the file
    if os.path.exists(app_path):
        with open(app_path, "r") as f:
            content = f.read()
        
        # Fix the import statement - replace the problematic import line completely
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if "import models" in line:
                fixed_lines.append("    import models  # Fixed import")
            else:
                fixed_lines.append(line)
        
        fixed_content = '\n'.join(fixed_lines)
        
        with open(app_path, "w") as f:
            f.write(fixed_content)
        
        print("Fixed import in app.py")
    
    # Create an environment wrapper to handle Python paths
    with open("test/.env.example", "r") as f:
        env_content = f.read()
    
    # Create a start_app.py in the test directory
    with open("test/start_app.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import and run the application
from main import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
""")
    
    print("Created start_app.py wrapper")
    
    # Run the application with the wrapper
    os.chdir("test")
    print(f"Working directory: {os.getcwd()}")
    
    # Run the Flask app directly with python -m
    print("Running Flask application...")
    subprocess.run([sys.executable, "main.py"])

if __name__ == "__main__":
    main()
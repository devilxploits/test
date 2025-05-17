#!/usr/bin/env python3
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

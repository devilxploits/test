
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
        f.write("# This file makes the directory a proper Python package\n")

# Run the main.py file
subprocess.run([sys.executable, "main.py"])

#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil

def clone_repository():
    """
    Clones the GitHub repository to the current directory.
    """
    repo_url = "https://github.com/devilxploits/test.git"
    temp_dir = "temp_repo"
    
    # Create a temporary directory for the clone
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    print(f"Cloning repository from {repo_url} to temporary directory...")
    try:
        # Clone the repository to the temporary directory
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        print("Repository successfully cloned to temporary directory.")
        
        # Move files from temp directory to main directory
        print("Moving files to main directory...")
        for item in os.listdir(temp_dir):
            source = os.path.join(temp_dir, item)
            destination = os.path.join(".", item)
            
            # If the destination already exists, remove it first
            if os.path.exists(destination):
                if os.path.isdir(destination):
                    shutil.rmtree(destination)
                else:
                    os.remove(destination)
            
            # Move the item
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
                
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
        print("Temporary directory cleaned up.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during repository deployment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clone_repository()
    
    # List files to verify the repository contents
    print("\nRepository contents:")
    for root, dirs, files in os.walk(".", topdown=True):
        # Skip the .git directory and our script directories
        if ".git" in dirs:
            dirs.remove(".git")
        if "temp_repo" in dirs:
            dirs.remove("temp_repo")
            
        level = root.replace("./", "").count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}{os.path.basename(root) or '.'}/")
        sub_indent = " " * 4 * (level + 1)
        for file in files:
            if file == "clone_repository.py" or file == "generated-icon.png":
                continue  # Skip listing our script
            print(f"{sub_indent}{file}")
    
    # Check if files were copied
    print("\nRepository has been successfully deployed to Replit.")
    print("The original file structure and all configurations have been preserved.")

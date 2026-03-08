#!/usr/bin/env python3
"""
FastAPI Project Initialization Script
=====================================

This script helps users quickly set up a new FastAPI project with
best practices and common patterns already in place.

Usage:
    python init_project.py
"""

import os
import sys
import shutil
import subprocess
import secrets
import string
from pathlib import Path

def get_user_input(prompt, default=None):
    """Get user input with default value support"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    response = input(prompt)
    return response if response.strip() else default

def generate_secret_key(length=32):
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def copy_template(template_dir, target_dir):
    """Copy template directory contents to target directory"""
    for item in template_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, target_dir)
        elif item.is_dir():
            shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)

def main():
    print("🚀 FastAPI Project Setup")
    print("=" * 50)

    # Get project name
    project_name = get_user_input("Project name", "fastapi-project")

    # Get project type
    print("\nSelect project type:")
    print("1. Hello World (minimal)")
    print("2. CRUD API (with database)")
    print("3. Auth API (with authentication)")

    choice = get_user_input("Choice (1-3)", "1")

    # Determine template based on choice
    template_map = {
        "1": "hello-world",
        "2": "crud-api",
        "3": "auth-api"
    }

    template_name = template_map.get(choice, "hello-world")
    template_path = Path(__file__).parent.parent / "assets" / "templates" / template_name

    if not template_path.exists():
        print(f"Error: Template '{template_name}' not found!")
        return 1

    # Create project directory
    project_dir = Path(project_name)
    if project_dir.exists():
        print(f"Error: Directory '{project_name}' already exists!")
        return 1

    project_dir.mkdir()
    print(f"📁 Created project directory: {project_dir}")

    # Copy template files
    print("📄 Copying template files...")
    copy_template(template_path, project_dir)

    # Generate secret key for auth templates
    if template_name == "auth-api":
        env_file = project_dir / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()

            # Replace placeholder with generated key
            secret_key = generate_secret_key()
            content = content.replace("your-secret-key-here-change-this-in-production", secret_key)

            with open(env_file, 'w') as f:
                f.write(content)

            print("🔑 Generated secure secret key")

    # Initialize git repo
    print("🔄 Initializing Git repository...")
    try:
        subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
        print("✅ Git repository initialized")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to initialize Git repository")

    # Create virtual environment
    print("🐍 Creating virtual environment...")
    try:
        venv_path = project_dir / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True, capture_output=True)
        print("✅ Virtual environment created")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to create virtual environment")

    # Install dependencies
    print("📦 Installing dependencies...")
    try:
        if sys.platform.startswith('win'):
            pip_cmd = project_dir / "venv" / "Scripts" / "pip"
        else:
            pip_cmd = project_dir / "venv" / "bin" / "pip"

        subprocess.run([str(pip_cmd), "install", "-r", str(project_dir / "requirements.txt")],
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to install dependencies")

    # Print next steps
    print("\n🎉 Project setup complete!")
    print(f"\n📁 Project directory: {project_dir.absolute()}")
    print("\nNext steps:")
    print("1. Navigate to project directory:")
    print(f"   cd {project_name}")
    print("2. Activate virtual environment:")
    if sys.platform.startswith('win'):
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("3. Set up environment variables:")
    print("   cp .env.example .env")
    print("4. Run database migrations (if applicable):")
    print("   python -c \"from app.database import create_db_and_tables; create_db_and_tables()\"")
    print("5. Run the application:")
    print("   uvicorn app.main:app --reload")
    print("\nFor detailed instructions, see the README.md file.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
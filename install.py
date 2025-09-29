#!/usr/bin/env python3
"""
Installation script for the Telegram Star Collector Bot
"""

import os
import sys
import subprocess
import json

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages. Please install manually:")
        print("pip install -r requirements.txt")
        return False

def setup_config():
    """Help user set up configuration"""
    print("\n⚙️  Setting up configuration...")
    
    config_file = "config.py"
    
    print("\nTo use this bot, you need to obtain:")
    print("1. Bot Token from @BotFather on Telegram")
    print("2. API ID and API Hash from https://my.telegram.org")
    
    get_credentials = input("\nDo you want to enter your credentials now? (y/n): ").lower().strip()
    
    if get_credentials == 'y':
        bot_token = input("Enter your Bot Token: ").strip()
        api_id = input("Enter your API ID: ").strip()
        api_hash = input("Enter your API Hash: ").strip()
        
        if bot_token and api_id and api_hash:
            # Read current config
            with open(config_file, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Replace values
            config_content = config_content.replace(
                'BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"',
                f'BOT_TOKEN = "{bot_token}"'
            )
            config_content = config_content.replace(
                'API_ID = 12345',
                f'API_ID = {api_id}'
            )
            config_content = config_content.replace(
                'API_HASH = "your_api_hash_here"',
                f'API_HASH = "{api_hash}"'
            )
            
            # Write updated config
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print("✅ Configuration updated successfully!")
        else:
            print("⚠️  Some values were empty. Please edit config.py manually.")
    else:
        print("⚠️  Please edit config.py manually with your credentials.")

def create_start_script():
    """Create a start script"""
    if os.name == 'nt':  # Windows
        script_name = "start_bot.bat"
        script_content = """@echo off
echo Starting Telegram Star Collector Bot...
python bot.py
pause
"""
    else:  # Unix-like
        script_name = "start_bot.sh"
        script_content = """#!/bin/bash
echo "Starting Telegram Star Collector Bot..."
python3 bot.py
"""
    
    with open(script_name, 'w') as f:
        f.write(script_content)
    
    if not os.name == 'nt':
        os.chmod(script_name, 0o755)
    
    print(f"✅ Created start script: {script_name}")

def main():
    """Main installation function"""
    print("🎯 Telegram Star Collector Bot - Installation")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        sys.exit(1)
    
    print(f"✅ Python {sys.version} detected")
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Installation failed!")
        sys.exit(1)
    
    # Setup configuration
    setup_config()
    
    # Create start script
    create_start_script()
    
    print("\n🎉 Installation completed!")
    print("\nNext steps:")
    print("1. Make sure you've updated config.py with your credentials")
    print("2. Run the bot using: python bot.py")
    print("   Or use the start script created for you")
    print("\n📚 For more information, check README.md")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Setup script for Attendance Notifier.

This script helps with initial setup, environment validation,
and basic configuration checks.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_whatsapp_python_library():
    """Check if whatsapp-python library is accessible."""
    try:
        # Add whatsapp-python to path
        whatsapp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'whatsapp-python')
        sys.path.insert(0, whatsapp_path)
        
        import whatsapp
        print("✅ whatsapp-python library found")
        return True
    except ImportError:
        print("❌ Error: whatsapp-python library not found")
        print("   Make sure the whatsapp-python directory exists in the parent directory")
        return False


def create_directories():
    """Create necessary directories."""
    directories = ['logs', 'tests', 'services', 'handlers']
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")


def check_env_file():
    """Check if .env file exists and is configured."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  .env file not found, but .env.example exists")
            print("   Copy .env.example to .env and configure your settings")
            return False
        else:
            print("❌ Error: Neither .env nor .env.example found")
            return False
    
    # Check if .env has required variables
    required_vars = [
        'WHATSAPP_TOKEN',
        'WHATSAPP_PHONE_NUMBER_ID', 
        'WHATSAPP_VERIFY_TOKEN',
        'WHATSAPP_RECIPIENT_NUMBER'
    ]
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=your_" in env_content or f"{var}=" in env_content.replace(f"{var}=\n", f"{var}="):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  .env file found but missing/incomplete variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ .env file configured")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def run_basic_tests():
    """Run basic configuration tests."""
    print("🧪 Running basic tests...")
    
    try:
        # Test imports
        from config import get_config
        config = get_config('testing')
        print("✅ Configuration loading works")
        
        # Test service initialization (with testing config)
        from services.whatsapp_service import WhatsAppService
        service = WhatsAppService(config.get_whatsapp_config())
        print("✅ WhatsApp service initialization works")
        
        return True
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Attendance Notifier Setup")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("WhatsApp Library", check_whatsapp_python_library),
        ("Directories", create_directories),
        ("Dependencies", install_dependencies),
        ("Environment File", check_env_file),
        ("Basic Tests", run_basic_tests)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure your .env file with WhatsApp API credentials")
        print("2. Run: python app.py")
        print("3. Test with: python tests/test_webhook.py")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
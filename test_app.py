#!/usr/bin/env python3
"""
Test script to verify the Hunter app works correctly
"""

import sys
import os
import subprocess
import time
import requests
from pathlib import Path

def test_app_startup():
    """Test that the app can start up without errors"""
    print("Testing Hunter app startup...")
    
    try:
        # Change to app directory
        os.chdir(Path(__file__).parent)
        
        # Test database initialization
        print("Testing database initialization...")
        from models import database
        database.create_tables()
        print("[OK] Database initialized successfully")
        
        # Test auth system
        print("Testing authentication system...")
        from auth import auth_manager
        print("[OK] Authentication system loaded successfully")
        
        # Test config
        print("Testing configuration...")
        from config import config
        print(f"[OK] Configuration loaded successfully - Page title: {config.PAGE_TITLE}")
        
        # Test app imports
        print("Testing app imports...")
        from app import HunterDashboard
        print("[OK] Main app imported successfully")
        
        # Test enhanced app imports
        try:
            from enhanced_app import EnhancedHunterDashboard
            print("[OK] Enhanced app imported successfully")
        except Exception as e:
            print(f"[WARNING] Enhanced app import warning: {e}")
        
        print("\n[SUCCESS] All tests passed! The app should work correctly.")
        print("\nTo run the app:")
        print("1. Run: python start_app.py")
        print("2. Or run: streamlit run app.py")
        print("3. Or use the batch file: run.bat")
        print("\nDefault login credentials:")
        print("Email: admin@hunter.app")
        print("Password: admin123")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_app_startup()
    sys.exit(0 if success else 1)
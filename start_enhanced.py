#!/usr/bin/env python3
"""
Hunter Enhanced Platform Launcher Script

This script starts the comprehensive Hunter platform with all enhanced features:
- Automated data pipeline
- Real-time scraping from App Store (all countries) and Steam
- Comprehensive events intelligence
- Cross-platform analysis
- Live dashboard with auto-refresh
"""

import sys
import os
import subprocess
import time
import threading
from pathlib import Path

def check_dependencies():
    """Check if enhanced dependencies are available"""
    required_packages = [
        'streamlit', 'fastapi', 'pandas', 'numpy', 'plotly', 
        'requests', 'bs4', 'schedule', 'sqlalchemy'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def initialize_enhanced_system():
    """Initialize the enhanced Hunter system"""
    print("Initializing Enhanced Hunter Platform...")
    
    try:
        # Initialize database
        print("Initializing database...")
        from models import database
        database.create_tables()
        
        # Initialize pipeline
        print("Initializing data pipeline...")
        from pipeline.data_pipeline import automated_pipeline
        
        # Start the automated pipeline
        print("Starting automated data pipeline...")
        automated_pipeline.start_pipeline()
        
        print("Enhanced system initialized successfully!")
        return True
        
    except Exception as e:
        print(f"System initialization failed: {e}")
        return False

def start_enhanced_dashboard():
    """Start the enhanced dashboard"""
    try:
        print("Starting Enhanced Hunter Dashboard...")
        print("Dashboard URL: http://localhost:8501")
        print("Default Login: admin@hunter.app / admin123")
        print("\nEnhanced Features Available:")
        print("  • Live Dashboard with Real-time Updates")  
        print("  • Comprehensive Scraping (App Store All Countries + Steam)")
        print("  • Events Intelligence from Multiple Sources")
        print("  • Cross-Platform Analysis")
        print("  • AI Success Predictions")
        print("  • Automated Data Pipeline")
        print("  • Advanced Analytics")
        print("\nPress Ctrl+C to stop all services\n")
        
        # Start Streamlit with enhanced app
        cmd = [
            sys.executable, "-m", "streamlit", "run", "enhanced_app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--server.headless=true"
        ]
        
        process = subprocess.Popen(cmd)
        
        # Wait for process
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nShutting down Enhanced Hunter Platform...")
            
            # Stop the pipeline
            try:
                from pipeline.data_pipeline import automated_pipeline
                automated_pipeline.stop_pipeline()
                print("Data pipeline stopped")
            except:
                pass
            
            # Stop Streamlit
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            
            print("Enhanced Hunter Platform stopped successfully")
        
    except Exception as e:
        print(f"Error starting enhanced dashboard: {e}")

def main():
    print("Hunter Enhanced Platform Launcher")
    print("=" * 50)
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("All dependencies available")
    
    # Initialize system
    if not initialize_enhanced_system():
        sys.exit(1)
    
    # Start enhanced dashboard
    start_enhanced_dashboard()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Simple Streamlit App Starter
Runs the Hunter Platform dashboard without the launcher complexity
"""

import os
import sys
from pathlib import Path

def main():
    """Start the Streamlit app directly"""
    print("Starting Hunter Platform Dashboard...")
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Initialize database
    try:
        from models import database
        database.create_tables()
        print("Database initialized")
    except Exception as e:
        print(f"Database warning: {e}")
    
    print("Streamlit dashboard starting...")
    print("Open your browser to: http://localhost:8501")
    print("Login: admin@hunter.app")
    print("Password: admin123")
    print("\nPress Ctrl+C to stop")
    
    # Start Streamlit app properly
    try:
        import subprocess
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=localhost"
        ]
        
        process = subprocess.run(cmd)
        
    except Exception as e:
        print(f"Error starting app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

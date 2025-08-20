#!/usr/bin/env python3
"""
Hunter Platform Launcher Script

This script provides an easy way to start the Hunter platform
with different configurations and modes.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import time

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import fastapi
        import sqlalchemy
        import pandas
        import numpy
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False

def setup_environment():
    """Set up environment variables"""
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path(".env.example")
        if env_example.exists():
            print("📝 Creating .env file from template...")
            import shutil
            shutil.copy(env_example, env_file)
        else:
            print("⚠️  No .env file found. Please create one with your configuration.")

def initialize_database():
    """Initialize the database"""
    try:
        print("🗄️  Initializing database...")
        from models import database
        database.create_tables()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_streamlit(host="localhost", port=8501):
    """Start the Streamlit dashboard"""
    print(f"🚀 Starting Streamlit dashboard on http://{host}:{port}")
    
    cmd = [
        "streamlit", "run", "app.py",
        "--server.port", str(port),
        "--server.address", host,
        "--server.headless", "true"
    ]
    
    return subprocess.Popen(cmd)

def start_api(host="localhost", port=8000):
    """Start the FastAPI server"""
    print(f"🔌 Starting API server on http://{host}:{port}")
    
    cmd = [
        "uvicorn", "api.main:app",
        "--host", host,
        "--port", str(port),
        "--reload"
    ]
    
    return subprocess.Popen(cmd)

def main():
    parser = argparse.ArgumentParser(description="Hunter Platform Launcher")
    parser.add_argument("--mode", choices=["dev", "api", "web", "full"], default="full",
                       help="Launch mode: dev (development), api (API only), web (Streamlit only), full (both)")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--web-port", type=int, default=8501, help="Streamlit port")
    parser.add_argument("--api-port", type=int, default=8000, help="API port")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency check")
    parser.add_argument("--skip-db", action="store_true", help="Skip database initialization")
    
    args = parser.parse_args()
    
    print("🎯 Hunter Platform Launcher")
    print("=" * 50)
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Check dependencies
    if not args.skip_deps and not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Initialize database
    if not args.skip_db and not initialize_database():
        sys.exit(1)
    
    processes = []
    
    try:
        if args.mode in ["full", "api", "dev"]:
            # Start API server
            api_process = start_api(args.host, args.api_port)
            processes.append(("API", api_process))
            
            if args.mode in ["full", "dev"]:
                # Wait a moment for API to start
                time.sleep(2)
        
        if args.mode in ["full", "web", "dev"]:
            # Start Streamlit
            web_process = start_streamlit(args.host, args.web_port)
            processes.append(("Streamlit", web_process))
        
        if processes:
            print("\n✅ Services started successfully!")
            print(f"📊 Dashboard: http://{args.host}:{args.web_port}")
            print(f"🔌 API: http://{args.host}:{args.api_port}")
            print(f"📚 API Docs: http://{args.host}:{args.api_port}/docs")
            print("\nDefault login credentials:")
            print("📧 Email: admin@hunter.app")
            print("🔑 Password: admin123")
            print("\nPress Ctrl+C to stop all services")
            
            # Wait for processes
            while True:
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"❌ {name} service stopped unexpectedly")
                        return
                time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
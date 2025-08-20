#!/usr/bin/env python3
"""
Hunter Platform Installation Script

This script helps install all dependencies for the Hunter platform,
with special handling for Python 3.12 compatibility.
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is supported"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3:
        print("ERROR: Python 3 is required")
        return False
    
    if version.minor < 8:
        print("ERROR: Python 3.8+ is required")
        return False
    
    if version.minor >= 12:
        print("SUCCESS: Python 3.12+ detected - using compatible dependencies")
    
    return True

def install_package(package, upgrade=False):
    """Install a single package with error handling"""
    try:
        cmd = [sys.executable, "-m", "pip", "install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {package}")
            return True
        else:
            print(f"❌ {package}: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {package}: {e}")
        return False

def install_requirements():
    """Install packages from requirements.txt with fallbacks"""
    print("📦 Installing required packages...")
    
    # Core packages that should install first
    core_packages = [
        "pip>=23.0.0",
        "setuptools>=65.0.0",
        "wheel>=0.38.0"
    ]
    
    print("\n🔧 Installing core build tools...")
    for package in core_packages:
        install_package(package, upgrade=True)
    
    # Main packages with Python 3.12 compatible versions
    packages = [
        "streamlit>=1.28.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
        "sqlalchemy>=2.0.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "plotly>=5.15.0",
        "altair>=5.0.0",
        "PyJWT>=2.8.0",
        "passlib[bcrypt]>=1.7.4",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "Pillow>=10.0.0"
    ]
    
    print("\n📊 Installing core application packages...")
    failed_packages = []
    
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # ML packages (might need special handling for Python 3.12)
    ml_packages = [
        "scikit-learn>=1.3.0",
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "sentence-transformers>=2.2.0"
    ]
    
    print("\n🧠 Installing ML packages...")
    for package in ml_packages:
        if not install_package(package):
            print(f"⚠️  {package} failed - you can install it later if needed")
    
    # Optional packages
    optional_packages = [
        "opencv-python>=4.8.0",
        "selenium>=4.15.0",
        "scrapy>=2.11.0"
    ]
    
    print("\n🔧 Installing optional packages...")
    for package in optional_packages:
        if not install_package(package):
            print(f"⚠️  {package} failed - skipping (optional)")
    
    return len(failed_packages) == 0

def create_environment_file():
    """Create .env file from example if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created - please review and update it with your settings")
    elif env_file.exists():
        print("📝 .env file already exists")
    else:
        print("⚠️  No .env.example file found")

def verify_installation():
    """Verify that key packages can be imported"""
    print("\n🔍 Verifying installation...")
    
    test_imports = [
        ("streamlit", "Streamlit dashboard"),
        ("fastapi", "FastAPI backend"),
        ("sqlalchemy", "Database ORM"),
        ("pandas", "Data processing"),
        ("numpy", "Numerical computing"),
        ("plotly", "Data visualization"),
        ("requests", "HTTP client")
    ]
    
    failed_imports = []
    
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - {module} not available")
            failed_imports.append(module)
    
    # Test optional imports
    optional_imports = [
        ("transformers", "NLP models"),
        ("torch", "PyTorch ML framework"),
        ("sklearn", "Scikit-learn"),
        ("cv2", "OpenCV")
    ]
    
    print("\n🔍 Checking optional packages...")
    for module, description in optional_imports:
        try:
            __import__(module)
            print(f"✅ {description}")
        except ImportError:
            print(f"⚠️  {description} - not available (optional)")
    
    return len(failed_imports) == 0

def main():
    print("Hunter Platform Installation Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Upgrade pip first
    print("⬆️  Upgrading pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    if not install_requirements():
        print("\n⚠️  Some packages failed to install, but continuing...")
    
    # Create environment file
    create_environment_file()
    
    # Verify installation
    success = verify_installation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Installation completed successfully!")
        print("\n📋 Next steps:")
        print("1. Review and update your .env file")
        print("2. Run: python run_app.py")
        print("3. Access dashboard at: http://localhost:8501")
        print("4. Default login: admin@hunter.app / admin123")
    else:
        print("⚠️  Installation completed with some issues")
        print("You may need to install missing packages manually")
        print("\nTry running: pip install -r requirements.txt")
    
    print("\n💡 For help, check the README.md file")

if __name__ == "__main__":
    import os
    main()
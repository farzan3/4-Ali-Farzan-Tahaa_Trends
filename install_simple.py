"""
Simple installation script for Hunter Platform (Python 3.12 compatible)
"""

import sys
import subprocess

def install_packages():
    """Install packages one by one with better error handling"""
    
    packages = [
        "streamlit",
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "pandas",
        "numpy", 
        "requests",
        "beautifulsoup4",
        "plotly",
        "PyJWT",
        "passlib[bcrypt]",
        "python-dotenv",
        "pydantic"
    ]
    
    print("Installing Hunter Platform dependencies...")
    print("Python version:", sys.version)
    
    # Upgrade pip first
    print("\nUpgrading pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    failed = []
    
    for package in packages:
        print(f"\nInstalling {package}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print(f"SUCCESS: {package}")
            else:
                print(f"FAILED: {package}")
                print(result.stderr)
                failed.append(package)
        except Exception as e:
            print(f"ERROR installing {package}: {e}")
            failed.append(package)
    
    print(f"\n{'='*50}")
    print(f"Installation Summary:")
    print(f"Successful: {len(packages) - len(failed)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print(f"Failed packages: {', '.join(failed)}")
    
    # Try to install optional ML packages
    print(f"\nInstalling optional ML packages...")
    ml_packages = ["scikit-learn", "transformers", "torch"]
    
    for package in ml_packages:
        print(f"\nTrying to install {package}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package], 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            if result.returncode == 0:
                print(f"SUCCESS: {package}")
            else:
                print(f"SKIPPED: {package} (optional)")
        except Exception as e:
            print(f"SKIPPED: {package} (optional) - {e}")
    
    return len(failed) == 0

if __name__ == "__main__":
    success = install_packages()
    
    print(f"\n{'='*50}")
    if success:
        print("Installation completed successfully!")
    else:
        print("Installation completed with some issues.")
        print("You can try running: pip install -r requirements-minimal.txt")
    
    print("\nNext steps:")
    print("1. Run: python run_app.py")
    print("2. Or directly: streamlit run app.py")
    print("3. Access at: http://localhost:8501")
    print("4. Login: admin@hunter.app / admin123")
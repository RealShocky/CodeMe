import os
from pathlib import Path
import sys
import site
import importlib.util
import subprocess

def find_package(package_name: str) -> bool:
    """Check if a package is installed in any Python path"""
    try:
        __import__(package_name.replace("-", "_"))
        return True
    except ImportError:
        return False

def check_environment():
    print("Checking CodeMe Assistant setup...")
    
    # Check Python version
    print(f"\nPython version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print("✅ Python version OK")

    # Try to import and load dotenv first
    try:
        from dotenv import load_dotenv
        env_path = Path('.env').absolute()
        load_dotenv(env_path)
        print(f"✅ Loaded .env file from {env_path}")
    except ImportError:
        print("❌ Could not import python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

    # Print Python paths for debugging
    print("\nPython paths:")
    for path in sys.path:
        print(f"  {path}")

    # Check project structure
    required_paths = [
        "src",
        "src/__init__.py",
        "src/main.py",
        "src/voice_assistant.py",
        "src/code_manager.py",
        "src/test_manager.py",
        "src/deployment_manager.py",
        "deployments/deployment_config.json",
        "requirements.txt",
        ".env"
    ]

    print("\nChecking project structure:")
    missing_paths = []
    for path in required_paths:
        if not Path(path).exists():
            missing_paths.append(path)
            print(f"❌ Missing: {path}")
        else:
            print(f"✅ Found: {path}")

    if missing_paths:
        print("\n❌ Some required files are missing!")
        return False

    # Check dependencies
    print("\nChecking dependencies...")
    required_packages = [
        "anthropic",
        "speech_recognition",
        "sounddevice",
        "numpy",
        "pytest",
        "docker",
        "autopep8",
        "python-dotenv"
    ]

    missing_packages = []
    for package in required_packages:
        if not find_package(package):
            missing_packages.append(package)
            print(f"❌ Missing package: {package}")
        else:
            print(f"✅ Found package: {package}")

    if missing_packages:
        print("\nInstall missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n❌ ANTHROPIC_API_KEY not found in environment")
        print("Current environment variables:")
        for key, value in os.environ.items():
            if "API" in key or "KEY" in key:
                print(f"  {key}: {value[:4]}...{value[-4:] if len(value) > 8 else ''}")
        return False
    else:
        masked_key = f"{api_key[:8]}...{api_key[-8:]}"
        print(f"\n✅ Found ANTHROPIC_API_KEY: {masked_key}")

    # Check microphone
    print("\nChecking microphone...")
    try:
        import speech_recognition as sr
        mic = sr.Microphone()
        print("✅ Microphone detected")
    except Exception as e:
        print(f"❌ Microphone error: {str(e)}")
        return False

    print("\nEnvironment variables:")
    for key, value in os.environ.items():
        if "PYTHON" in key or "PATH" in key:
            print(f"  {key}: {value}")

    print("\n✅ All checks passed! You can now run the assistant with:")
    print("python src/main.py")
    return True

if __name__ == "__main__":
    check_environment()
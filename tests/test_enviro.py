from pathlib import Path
import os
from dotenv import load_dotenv

def test_env():
    print("Current working directory:", os.getcwd())
    
    env_path = Path('.env')
    print("\n.env file exists:", env_path.exists())
    
    if env_path.exists():
        print("\nContents of .env file:")
        with open('.env', 'rb') as f:
            content = f.read()
            print("Raw bytes:", content)
            print("Decoded:", content.decode('utf-8'))
    
    print("\nTrying to load .env")
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    print("\nAPI Key loaded:", "Yes" if api_key else "No")
    if api_key:
        print("API Key starts with:", api_key[:10])

if __name__ == "__main__":
    test_env()
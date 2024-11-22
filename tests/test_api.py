import os
from dotenv import load_dotenv
import requests
import json

def test_api_detailed():
    print("Testing Anthropic API with detailed output...")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    print(f"\nAPI Key found: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key: {api_key[:15]}...{api_key[-5:]}")
    
    # Make a direct API call to test authentication
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 10,
        "messages": [{
            "role": "user",
            "content": "Say hello"
        }]
    }
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        print("\nAPI Response Details:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"\nError making API request: {e}")

if __name__ == "__main__":
    test_api_detailed()
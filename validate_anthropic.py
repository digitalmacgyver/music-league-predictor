#!/usr/bin/env ./venv/bin/python3
"""
Quick Anthropic API key validator
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

def main():
    """Validate existing Anthropic API key"""
    
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    print("🧠 ANTHROPIC API KEY VALIDATOR")
    print("=" * 40)
    
    if not api_key:
        print("❌ No Anthropic API key found in .env file")
        print("💡 Run ./setup_anthropic.py to set up your key")
        return
    
    print(f"Found API key in .env file:")
    print(f"Key: {api_key[:12]}...{api_key[-8:] if len(api_key) > 20 else api_key}")
    print()
    
    try:
        # Test API key
        print("Testing API connection...")
        client = Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'API working' and nothing else"}]
        )
        
        if response and response.content:
            response_text = response.content[0].text.strip()
            print(f"✅ API works! Response: '{response_text}'")
            
            # Test usage tracking
            print(f"✅ Model: {response.model}")
            print(f"✅ Input tokens: {response.usage.input_tokens}")
            print(f"✅ Output tokens: {response.usage.output_tokens}")
            
            print("\n🎉 Anthropic API is fully functional!")
            print("Your forecasting system now has advanced theme analysis.")
        else:
            print("❌ No response from API")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        if "authentication" in str(e).lower():
            print("💡 API key is invalid - check your key in .env file")
        elif "credit" in str(e).lower():
            print("💡 Check your account credits at https://console.anthropic.com/")
        print("💡 Run ./setup_anthropic.py to reconfigure")

if __name__ == "__main__":
    main()
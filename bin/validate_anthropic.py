#!/usr/bin/env python3
"""
Quick Anthropic API key validator
"""

import os
import sys
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from dotenv import load_dotenv
from anthropic import Anthropic
from cached_llm_client import CachedAnthropicClient

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
        cached_client = CachedAnthropicClient(verbose=True)
        
        response_text = cached_client.create_message_simple(
            prompt="Say 'API working' and nothing else",
            model="claude-3-5-haiku-20241022",
            max_tokens=50,
            temperature=0.0
        )
        
        if response_text:
            print(f"✅ API works! Response: '{response_text.strip()}'")
            
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
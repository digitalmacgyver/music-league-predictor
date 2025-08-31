#!/usr/bin/env python3
"""
Quick Anthropic API key validator
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

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
    
    print(f"✅ Found API key in .env file:")
    print(f"   Key: {api_key[:12]}...{api_key[-8:] if len(api_key) > 20 else api_key}")
    print()
    
    # Try to import and test the cached client
    try:
        from music_league.cached_llm_client import CachedAnthropicClient
        print("✅ CachedAnthropicClient module imports successfully")
        
        # Test API key
        print("\nTesting API connection...")
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
            
    except ImportError as e:
        if "anthropic" in str(e):
            print("⚠️  The 'anthropic' Python module is not installed")
            print("   However, the API key is configured in .env")
            print("   Scout may still work if it has alternative API access methods")
        else:
            print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ API test failed: {e}")
        if "authentication" in str(e).lower():
            print("💡 API key is invalid - check your key in .env file")
        elif "credit" in str(e).lower():
            print("💡 Check your account credits at https://console.anthropic.com/")
        else:
            print("💡 Run ./setup_anthropic.py to reconfigure")

if __name__ == "__main__":
    main()
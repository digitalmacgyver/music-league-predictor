#!/usr/bin/env ./venv/bin/python3
"""
Anthropic API Key Setup Guide and Tester
For Claude Max subscribers to get API access
"""

import os
import webbrowser
from pathlib import Path
import json
from anthropic import Anthropic
import logging

logger = logging.getLogger(__name__)

def print_api_key_instructions():
    """Print instructions for getting Anthropic API keys"""
    print("🧠 ANTHROPIC API KEY SETUP")
    print("=" * 50)
    print()
    print("As a Claude Max subscriber, you can get API access:")
    print()
    print("1. Go to: https://console.anthropic.com/")
    print("2. Log in with your Anthropic account (same as Claude subscription)")
    print("3. Navigate to 'API Keys' in the left sidebar")
    print("4. Click 'Create Key'")
    print("5. Give it a name like 'Music League Forecaster'")
    print("6. Copy the generated key (starts with 'sk-ant-')")
    print()
    print("Important notes:")
    print("- API usage has separate billing from your Claude subscription")
    print("- You get $5 free credit to start")
    print("- Our forecasting system uses minimal tokens per prediction")
    print("- Claude 3.5 Haiku costs ~$0.25 per 1M input tokens")
    print()

def open_anthropic_console():
    """Open Anthropic Console in browser"""
    try:
        webbrowser.open("https://console.anthropic.com/")
        print("✅ Opened Anthropic Console in your browser")
        return True
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print("Please manually visit: https://console.anthropic.com/")
        return False

def prompt_for_api_key():
    """Interactively prompt for API key"""
    print("\n🔑 API KEY SETUP")
    print("=" * 50)
    
    print("Enter your Anthropic API key:")
    api_key = input("API Key (starts with sk-ant-): ").strip()
    
    if not api_key:
        print("❌ API key is required")
        return None
    
    if not api_key.startswith('sk-ant-'):
        print("⚠️  Warning: API key should start with 'sk-ant-'")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            return None
    
    return api_key

def test_anthropic_key(api_key):
    """Test if the API key works"""
    print("\n🧪 TESTING API KEY")
    print("=" * 50)
    
    try:
        # Initialize client
        client = Anthropic(api_key=api_key)
        
        # Test with a simple request
        print("Testing API connection...")
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=50,
            messages=[{
                "role": "user", 
                "content": "Respond with exactly: API test successful"
            }]
        )
        
        if response and response.content:
            response_text = response.content[0].text.strip()
            print(f"✅ Success! Response: '{response_text}'")
            
            # Test theme analysis (what we'll actually use)
            print("\nTesting theme analysis...")
            theme_response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": """Analyze this Music League theme: "Songs about travel"
                    
                    Respond in JSON format:
                    {"emotional_tone": "adventurous", "energy_level": "medium", "success_factors": ["movement", "journey"]}"""
                }]
            )
            
            if theme_response and theme_response.content:
                theme_text = theme_response.content[0].text.strip()
                print(f"✅ Theme analysis works!")
                print(f"   Sample response: {theme_text[:100]}...")
                return True
            else:
                print("❌ Theme analysis failed")
                return False
        else:
            print("❌ No response from API")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        if "authentication" in str(e).lower():
            print("💡 This usually means the API key is invalid")
        elif "rate limit" in str(e).lower():
            print("💡 Rate limit reached - try again in a moment")
        elif "credit" in str(e).lower():
            print("💡 You may need to add credits to your account")
        return False

def save_api_key_to_env(api_key):
    """Save API key to .env file"""
    env_path = Path(".env")
    
    # Read existing .env content if it exists
    existing_content = ""
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Filter out existing Anthropic API key
        filtered_lines = []
        for line in lines:
            if not line.startswith('ANTHROPIC_API_KEY='):
                filtered_lines.append(line)
        
        existing_content = ''.join(filtered_lines)
    
    # Add new API key
    anthropic_config = f"""
# Anthropic API key for theme analysis
ANTHROPIC_API_KEY={api_key}
"""
    
    # Write the updated .env file
    with open(env_path, 'w') as f:
        f.write(existing_content.rstrip() + anthropic_config)
    
    print(f"✅ API key saved to {env_path}")
    print("🧠 Advanced LLM theme analysis is now enabled!")

def test_forecasting_integration():
    """Test the forecasting system with Anthropic API"""
    print("\n🔮 TESTING FORECASTING INTEGRATION")
    print("=" * 50)
    
    try:
        from forecasting import MusicForecaster
        
        forecaster = MusicForecaster()
        
        if forecaster.anthropic_client is None:
            print("❌ Forecasting system shows Anthropic as unavailable")
            print("💡 Try restarting or check .env file")
            return False
        
        # Test theme analysis
        print("Testing theme analysis...")
        theme_analysis = forecaster.analyze_theme_with_llm(
            "Songs about love", 
            "Submit songs about romantic love, heartbreak, or relationships"
        )
        
        print(f"✅ Success! Theme analysis:")
        print(f"   Emotional tone: {theme_analysis.emotional_tone}")
        print(f"   Energy level: {theme_analysis.energy_level}")
        print(f"   Success factors: {', '.join(theme_analysis.success_factors[:3])}")
        
        forecaster.close()
        return True
        
    except Exception as e:
        print(f"❌ Forecasting integration test failed: {e}")
        return False

def main():
    """Main setup flow"""
    logging.basicConfig(level=logging.INFO)
    
    print_api_key_instructions()
    
    # Ask if user wants to open console
    response = input("Open Anthropic Console to get API key? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        open_anthropic_console()
        print("\nAfter creating your API key, come back here...")
        input("Press Enter when ready to continue...")
    
    # Get API key
    api_key = prompt_for_api_key()
    if not api_key:
        print("❌ Setup cancelled")
        return
    
    # Test API key
    if not test_anthropic_key(api_key):
        print("❌ API key test failed. Please check your key.")
        print("💡 Make sure you copied the complete key from the console")
        return
    
    # Save to .env file
    save_api_key_to_env(api_key)
    
    # Test forecasting integration
    test_forecasting_integration()
    
    print("\n🎉 ANTHROPIC SETUP COMPLETE!")
    print("=" * 50)
    print("Your forecasting system now has advanced LLM theme analysis:")
    print("- Sophisticated understanding of abstract themes")
    print("- Better prediction of what voters will like")
    print("- More nuanced musical characteristic matching")
    print()
    print("Test enhanced predictions:")
    print("  ./venv/bin/python3 predict_food_theme.py")

if __name__ == "__main__":
    main()
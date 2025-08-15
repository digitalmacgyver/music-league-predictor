#!/usr/bin/env ./venv/bin/python3
"""
Debug the theme analysis to see what Opus is returning
"""

import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

def debug_theme_analysis():
    """Debug what Opus returns for theme analysis"""
    
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    theme_title = "Ominous rock"
    theme_description = "Rock songs that sound dark, foreboding, or threatening"
    
    prompt = f"""
    Analyze this Music League round theme and predict what types of songs would be successful:

    Theme Title: {theme_title}
    Theme Description: {theme_description}

    Please analyze:
    1. The emotional tone/mood this theme suggests
    2. Musical characteristics that would fit (tempo, energy, genre elements)
    3. Specific genres that might work well
    4. Overall energy level (high/medium/low)
    5. Key thematic keywords for matching
    6. Success factors for song selection

    Respond in JSON format with these fields:
    - emotional_tone: string describing the mood
    - musical_characteristics: array of musical elements
    - genre_preferences: array of genres
    - energy_level: "high", "medium", or "low"
    - thematic_keywords: array of relevant keywords
    - success_factors: array of what makes songs succeed for this theme
    """
    
    print("🔍 DEBUGGING THEME ANALYSIS")
    print("=" * 50)
    print(f"Theme: {theme_title}")
    print(f"Description: {theme_description}")
    print()
    
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        print("Raw Opus Response:")
        print("-" * 30)
        print(response_text)
        print("-" * 30)
        print()
        
        # Try to parse as JSON
        try:
            parsed_json = json.loads(response_text)
            print("✅ JSON parsing successful!")
            print("Parsed structure:")
            for key, value in parsed_json.items():
                print(f"  {key}: {value}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print("The response is not valid JSON format")
            
            # Try to extract JSON if it's embedded
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                print("\nTrying to extract embedded JSON...")
                try:
                    embedded_json = json.loads(json_match.group())
                    print("✅ Embedded JSON extraction successful!")
                    for key, value in embedded_json.items():
                        print(f"  {key}: {value}")
                except:
                    print("❌ Embedded JSON extraction also failed")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")

if __name__ == "__main__":
    debug_theme_analysis()
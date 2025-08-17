#!/usr/bin/env ./venv/bin/python3
"""
Debug the theme analysis to see what Opus is returning
"""

import os
import sys
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

import json
from anthropic import Anthropic
from dotenv import load_dotenv
from cached_llm_client import CachedAnthropicClient

load_dotenv()

def debug_theme_analysis():
    """Debug what Opus returns for theme analysis"""
    
    cached_client = CachedAnthropicClient(verbose=True)
    
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
        response_text = cached_client.create_message_simple(
            prompt=prompt,
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.7
        )
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
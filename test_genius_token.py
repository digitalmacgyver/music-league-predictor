#!/usr/bin/env ./venv/bin/python3
"""
Test script to verify Genius API token is working
"""

import os
from dotenv import load_dotenv
import lyricsgenius

load_dotenv()

def test_genius_token():
    # Try both possible token names
    token = os.getenv('GENIUS_CLIENT_ACCESS_TOKEN') or os.getenv('GENIUS_ACCESS_TOKEN')
    
    if not token:
        print("❌ GENIUS_CLIENT_ACCESS_TOKEN not found in .env file")
        print("\n📝 To add it:")
        print("1. Get your token from https://genius.com/api-clients")
        print("2. Edit .env file and add:")
        print("   GENIUS_CLIENT_ACCESS_TOKEN=your_token_here")
        return False
    
    print(f"✅ Token found: {token[:10]}...")
    print("🔍 Testing API connection...")
    
    try:
        genius = lyricsgenius.Genius(token, timeout=10)
        genius.verbose = False
        
        # Test with a famous song
        song = genius.search_song("Don't Stop Believin'", "Journey")
        
        if song:
            print(f"✅ API working! Found: {song.title} by {song.artist}")
            print(f"   Lyrics preview: {song.lyrics[:100]}...")
            
            # Test another one
            song2 = genius.search_song("Pictures of You", "The Cure")
            if song2:
                print(f"✅ Also found: {song2.title} by {song2.artist}")
            
            return True
        else:
            print("⚠️ API connected but couldn't find test song")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🎵 Genius API Token Test")
    print("=" * 40)
    
    if test_genius_token():
        print("\n🎉 Success! Your Genius API is ready to use")
        print("Scout will now fetch real lyrics for analysis")
    else:
        print("\n💡 Once you add the token, Scout will have access to")
        print("   millions of song lyrics for better theme matching!")
#!/usr/bin/env ./venv/bin/python3
"""
Debug Spotipy URL construction issue
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable verbose logging
logging.basicConfig(level=logging.DEBUG)

def debug_spotipy_urls():
    """Debug how Spotipy constructs URLs"""
    
    # Load credentials
    if not os.getenv('SPOTIFY_CLIENT_ID'):
        print("❌ No Spotify credentials found")
        return
    
    print("🔍 DEBUGGING SPOTIPY URL CONSTRUCTION")
    print("=" * 50)
    
    # Initialize Spotify client
    client_credentials_manager = SpotifyClientCredentials(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # First test: successful search
    print("\n1. Testing search (usually works):")
    try:
        results = sp.search(q="Come Together The Beatles", type='track', limit=1)
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            track_id = track['id']
            print(f"✅ Search successful: {track['name']} by {track['artists'][0]['name']}")
            print(f"   Track ID: {track_id}")
            
            # Now test audio_features
            print(f"\n2. Testing audio_features with track ID: {track_id}")
            
            # Let's examine the client's base URL
            print(f"   Spotipy base URL: {sp._base_url}")
            
            # Try to intercept the actual URL being called
            original_get = sp._get
            
            def debug_get(url, args=None, payload=None, **kwargs):
                print(f"   🔍 INTERCEPTED GET REQUEST:")
                print(f"      URL: {url}")
                print(f"      Args: {args}")
                print(f"      Payload: {payload}")
                print(f"      Kwargs: {kwargs}")
                
                # Call original method
                return original_get(url, args, payload, **kwargs)
            
            sp._get = debug_get
            
            try:
                features = sp.audio_features([track_id])
                print(f"✅ Audio features call successful!")
                if features and features[0]:
                    print(f"   Energy: {features[0]['energy']:.2f}")
            except Exception as e:
                print(f"❌ Audio features failed: {e}")
                
        else:
            print("❌ No tracks found in search")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")

def test_direct_api_call():
    """Test direct API call to Spotify"""
    
    print(f"\n3. Testing direct HTTP call to Spotify API:")
    
    # Get access token
    client_credentials_manager = SpotifyClientCredentials(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
    )
    
    token_info = client_credentials_manager.get_access_token()
    access_token = token_info['access_token']
    
    # Make direct request
    track_id = "2EqlS6tkEnglzr7tkKAAYD"  # Come Together by The Beatles
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    # Correct URL format
    correct_url = f"https://api.spotify.com/v1/audio-features?ids={track_id}"
    print(f"   Trying correct URL: {correct_url}")
    
    response = requests.get(correct_url, headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    
    # Also try the malformed URL that Spotipy seems to generate
    malformed_url = f"https://api.spotify.com/v1/audio-features/?ids={track_id}"
    print(f"\n   Trying malformed URL: {malformed_url}")
    
    response2 = requests.get(malformed_url, headers=headers)
    print(f"   Status: {response2.status_code}")
    print(f"   Response: {response2.text[:200]}...")

if __name__ == "__main__":
    debug_spotipy_urls()
    test_direct_api_call()
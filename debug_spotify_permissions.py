#!/usr/bin/env ./venv/bin/python3
"""
Debug Spotify API permissions and capabilities
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from dotenv import load_dotenv

load_dotenv()

def test_spotify_endpoints():
    """Test various Spotify endpoints to understand permissions"""
    
    if not os.getenv('SPOTIFY_CLIENT_ID'):
        print("❌ No Spotify credentials found")
        return
    
    print("🔍 TESTING SPOTIFY API ENDPOINTS")
    print("=" * 50)
    
    # Initialize client
    client_credentials_manager = SpotifyClientCredentials(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Get access token info
    token_info = client_credentials_manager.get_access_token()
    print(f"Access token expires in: {token_info.get('expires_in', 'unknown')} seconds")
    print(f"Token type: {token_info.get('token_type', 'unknown')}")
    
    test_track_id = "2EqlS6tkEnglzr7tkKAAYD"  # Come Together by The Beatles
    
    # Test different endpoints
    endpoints_to_test = [
        ("search", lambda: sp.search(q="Come Together The Beatles", type='track', limit=1)),
        ("track info", lambda: sp.track(test_track_id)),
        ("artist info", lambda: sp.artist("3WrFJ7ztbogyGnTHbHJFl2")),  # The Beatles
        ("audio_features", lambda: sp.audio_features([test_track_id])),
        ("audio_analysis", lambda: sp.audio_analysis(test_track_id)),
    ]
    
    for name, test_func in endpoints_to_test:
        print(f"\n{name.upper()}:")
        try:
            result = test_func()
            if result:
                print(f"  ✅ Success!")
                if name == "audio_features" and result[0]:
                    features = result[0]
                    print(f"     Energy: {features['energy']:.2f}")
                    print(f"     Valence: {features['valence']:.2f}")
                elif name == "track info":
                    print(f"     Track: {result['name']} by {result['artists'][0]['name']}")
                elif name == "search":
                    if result['tracks']['items']:
                        track = result['tracks']['items'][0]
                        print(f"     Found: {track['name']} by {track['artists'][0]['name']}")
            else:
                print(f"  ⚠️ Returned empty result")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            if "403" in str(e):
                print(f"     This suggests insufficient permissions for this endpoint")
            elif "429" in str(e):
                print(f"     This suggests rate limiting")

def check_app_permissions():
    """Check what our Spotify app is authorized for"""
    
    print(f"\n🔧 SPOTIFY APP CONFIGURATION CHECK")
    print("=" * 50)
    
    print(f"Your Spotify app needs these settings:")
    print(f"1. Go to https://developer.spotify.com/dashboard")
    print(f"2. Select your app (client ID: {os.getenv('SPOTIFY_CLIENT_ID', 'unknown')[:12]}...)")
    print(f"3. Check 'Settings' to ensure it's set up for Web API access")
    print(f"4. For audio-features endpoint, you may need:")
    print(f"   - Web API access (which you should have)")
    print(f"   - No special quota approval needed for basic features")
    print(f"   - But some advanced features require approval")
    
    print(f"\nIf audio-features still fails with 403:")
    print(f"• Your app might be restricted to basic endpoints only")
    print(f"• Try creating a new Spotify app")
    print(f"• Check if your region/account has restrictions")
    print(f"• Contact Spotify developer support")

if __name__ == "__main__":
    test_spotify_endpoints()
    check_app_permissions()
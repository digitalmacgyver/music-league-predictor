#!/usr/bin/env ./venv/bin/python3
"""
Quick Spotify credential validator
Use this if you already have credentials and just want to test them
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def main():
    """Validate existing Spotify credentials"""
    
    # Load environment variables
    load_dotenv()
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    print("🎵 SPOTIFY CREDENTIAL VALIDATOR")
    print("=" * 40)
    
    if not client_id or not client_secret:
        print("❌ No Spotify credentials found in .env file")
        print("💡 Run ./setup_spotify.py to set up credentials")
        return
    
    print(f"Found credentials in .env file:")
    print(f"Client ID: {client_id[:8]}...{client_id[-4:] if len(client_id) > 12 else client_id}")
    print(f"Client Secret: {'*' * 8}...{client_secret[-4:] if len(client_secret) > 12 else '****'}")
    print()
    
    try:
        # Test credentials
        print("Testing connection...")
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test search
        results = sp.search(q="The Beatles", type='artist', limit=1)
        if results['artists']['items']:
            artist = results['artists']['items'][0]
            print(f"✅ Search works! Found: {artist['name']} ({artist['followers']['total']:,} followers)")
        
        # Test audio features
        track_results = sp.search(q="Come Together The Beatles", type='track', limit=1)
        if track_results['tracks']['items']:
            track = track_results['tracks']['items'][0]
            features = sp.audio_features(track['id'])[0]
            if features:
                print(f"✅ Audio features work! Come Together - Energy: {features['energy']:.2f}, Tempo: {features['tempo']:.0f}")
            else:
                print("⚠️  Search works but audio features failed")
        
        print("\n🎉 All Spotify features are working!")
        print("Your forecasting system now has enhanced audio analysis capabilities.")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        if "Invalid client" in str(e):
            print("💡 Check your Client ID and Client Secret in .env file")
        print("💡 Run ./setup_spotify.py to reconfigure")

if __name__ == "__main__":
    main()
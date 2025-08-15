#!/usr/bin/env ./venv/bin/python3
"""
Debug Spotipy URL construction and compare with raw requests
"""

import os
import logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_spotipy_vs_raw():
    """Compare Spotipy behavior with our raw requests"""
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.error("Missing Spotify credentials")
        return
    
    # Test with Spotipy
    logger.info("🎵 Testing with Spotipy library...")
    
    try:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test search first
        logger.info("Testing Spotipy search...")
        search_results = sp.search(q="rock", type="track", limit=5)
        track_count = len(search_results['tracks']['items'])
        logger.info(f"✅ Spotipy search successful - found {track_count} tracks")
        
        if search_results['tracks']['items']:
            track = search_results['tracks']['items'][0]
            track_id = track['id']
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            
            logger.info(f"Testing audio features for: {track_name} by {artist_name} (ID: {track_id})")
            
            # Test audio features - this is where the 403 occurs
            try:
                features = sp.audio_features([track_id])
                if features and features[0]:
                    logger.info(f"✅ Spotipy audio features successful!")
                    logger.info(f"Energy: {features[0]['energy']}, Danceability: {features[0]['danceability']}")
                else:
                    logger.error("❌ Spotipy audio features returned None/empty")
            except Exception as e:
                logger.error(f"❌ Spotipy audio features failed: {e}")
                
                # Check if it's a 403 by looking at the exception
                if "403" in str(e):
                    logger.info("This is the same 403 error we see with raw requests")
                
    except Exception as e:
        logger.error(f"❌ Spotipy setup failed: {e}")

def test_permissions_theory():
    """Test if the issue is related to Spotify app permissions/settings"""
    
    logger.info("🔍 Investigating potential permission issues...")
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    logger.info(f"Client ID: {client_id}")
    
    # The audio features endpoint requires specific API access
    # Let's check what endpoints work vs don't work
    
    logger.info("📋 Summary of what we know:")
    logger.info("✅ Working endpoints:")
    logger.info("   - Token acquisition (accounts.spotify.com)")
    logger.info("   - Search (/v1/search)")
    logger.info("   - Track info (/v1/tracks/{id})")
    
    logger.info("❌ Failing endpoints:")
    logger.info("   - Audio features (/v1/audio-features/{id})")
    logger.info("   - Batch audio features (/v1/audio-features)")
    
    logger.info("🤔 Possible causes:")
    logger.info("1. Audio features require special app permissions in Spotify Dashboard")
    logger.info("2. Our app registration doesn't have 'Audio Features' scope enabled")
    logger.info("3. Spotify may have changed permissions for Client Credentials flow")
    logger.info("4. These endpoints may now require user authentication instead of client credentials")

def main():
    """Run debugging tests"""
    
    print("🔬 Spotipy vs Raw Requests Debugging")
    print("=" * 40)
    
    test_spotipy_vs_raw()
    
    print("\n" + "=" * 40)
    test_permissions_theory()

if __name__ == "__main__":
    main()
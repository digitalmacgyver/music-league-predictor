#!/usr/bin/env python3
"""
Test UUID filtering with a song that should be an exact match
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from forecasting import MusicForecaster
from spotify_utils import SpotifyUtils

def test_exact_uuid_match():
    """Test UUID filtering with exact Spotify ID match"""
    
    print("Testing Exact UUID Match Filtering")
    print("=" * 35)
    
    forecaster = MusicForecaster()
    
    # Create a candidate that should match exactly what's in our database
    test_candidates = [
        {"title": "Sundown", "artist": "Gordon Lightfoot"},  # Should be filtered
        {"title": "Test Fake Song", "artist": "Test Fake Artist"}  # Should not be found
    ]
    
    print("Input candidates:")
    for candidate in test_candidates:
        print(f"  • {candidate['title']} by {candidate['artist']}")
    
    # Check what Spotify returns for Sundown
    if forecaster.spotify:
        print(f"\nSpotify search for 'Sundown' by Gordon Lightfoot:")
        try:
            results = forecaster.spotify.search(q='track:"Sundown" artist:"Gordon Lightfoot"', type='track', limit=3)
            tracks = results.get('tracks', {}).get('items', [])
            
            for track in tracks:
                print(f"  📀 {track['name']} by {', '.join([a['name'] for a in track['artists']])}")
                print(f"     ID: {track['id']}")
                print(f"     Album: {track['album']['name']}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test the filtering
    print(f"\nTesting UUID filtering...")
    filtered = forecaster.filter_by_spotify_uuid(test_candidates)
    
    print(f"\nResults:")
    print(f"  Input: {len(test_candidates)} candidates")
    print(f"  Output: {len(filtered)} candidates")
    
    for candidate in filtered:
        spotify_id = candidate.get('spotify_track_id', 'unknown')
        print(f"  ✅ PASSED: {candidate['title']} by {candidate['artist']} (ID: {spotify_id})")
    
    # Check if Sundown's ID is in our existing cache
    sundown_id = SpotifyUtils.extract_track_id("https://open.spotify.com/track/0SjnBEHZVXgCKvOrpvzL2k")
    print(f"\nDatabase check:")
    print(f"  Sundown Spotify ID from DB: {sundown_id}")
    print(f"  ID in existing cache: {'✅ YES' if sundown_id in forecaster.existing_spotify_ids else '❌ NO'}")

if __name__ == "__main__":
    test_exact_uuid_match()
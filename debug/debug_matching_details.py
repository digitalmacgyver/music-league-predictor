#!/usr/bin/env ./venv/bin/python3
"""
Debug the specific matching logic in detail
"""

import os
import logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from candidate_verification import CandidateVerifier

load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_detailed_matching():
    """Test the detailed matching logic step by step"""
    print("🔍 Detailed Matching Analysis")
    print("=" * 70)
    
    # Initialize Spotify client
    client_credentials_manager = SpotifyClientCredentials(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
    )
    spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    verifier = CandidateVerifier()
    
    title = "It's Raining Tacos"
    artist = "Parry Gripp"
    
    # Get search results
    query = f'{title} {artist}'
    results = spotify.search(q=query, type='track', limit=10)
    
    norm_title = verifier.normalize_title(title).lower()
    norm_artist = verifier.normalize_artist(artist).lower()
    
    print(f"Looking for: '{norm_title}' by '{norm_artist}'")
    print()
    
    for i, track in enumerate(results['tracks']['items']):
        if not track or not track.get('name') or not track.get('artists'):
            continue
        
        track_title = verifier.normalize_title(track['name']).lower()
        track_artist = verifier.normalize_artist(track['artists'][0]['name']).lower()
        
        print(f"Track {i+1}: '{track_title}' by '{track_artist}'")
        
        # Test exact match
        title_match = 1.0 if track_title == norm_title else 0.0
        print(f"  Exact title match: {title_match}")
        
        # Test prefix removal if no exact match
        if title_match == 0.0:
            common_prefixes = ["it's ", "its ", "the ", "a ", "an "]
            title_no_prefix = norm_title
            track_no_prefix = track_title
            
            print(f"  Before prefix removal:")
            print(f"    Input title: '{title_no_prefix}'")
            print(f"    Track title: '{track_no_prefix}'")
            
            for prefix in common_prefixes:
                if title_no_prefix.startswith(prefix):
                    title_no_prefix = title_no_prefix[len(prefix):]
                    print(f"    Removed '{prefix}' from input: '{title_no_prefix}'")
                if track_no_prefix.startswith(prefix):
                    track_no_prefix = track_no_prefix[len(prefix):]
                    print(f"    Removed '{prefix}' from track: '{track_no_prefix}'")
            
            print(f"  After prefix removal:")
            print(f"    Input title: '{title_no_prefix}'")
            print(f"    Track title: '{track_no_prefix}'")
            
            if title_no_prefix == track_no_prefix and len(title_no_prefix) > 3:
                title_match = 0.85
                print(f"  ✅ Prefix match! Score: {title_match}")
            else:
                print(f"  ❌ No prefix match")
        
        # Test artist match
        artist_match = 1.0 if track_artist == norm_artist else 0.0
        print(f"  Artist match: {artist_match}")
        
        # Calculate total score
        score = (title_match * 0.7 + artist_match * 0.3)
        print(f"  Total score: {score:.3f} (threshold: 0.8)")
        
        if score >= 0.8:
            print(f"  ✅ WOULD ACCEPT THIS MATCH")
        else:
            print(f"  ❌ Below threshold")
        
        print()

def main():
    """Run detailed matching test"""
    test_detailed_matching()

if __name__ == "__main__":
    main()
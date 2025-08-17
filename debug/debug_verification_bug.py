#!/usr/bin/env ./venv/bin/python3
"""
Debug why verification is failing despite good matches
"""

import os
import logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

def debug_verification_step_by_step():
    """Step through the exact verification logic"""
    print("🐛 Step-by-step Verification Debug")
    print("=" * 70)
    
    # Initialize Spotify client
    client_credentials_manager = SpotifyClientCredentials(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
    )
    spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    title = "It's Raining Tacos"
    artist = "Parry Gripp"
    
    print(f"Verifying: '{title}' by '{artist}'")
    
    # Simulate the exact verification logic
    try:
        # Try exact search first
        query = f'track:"{title}" artist:"{artist}"'
        results = spotify.search(q=query, type='track', limit=5)
        
        print(f"\n1. Exact search: {query}")
        print(f"   Found {len(results['tracks']['items'])} results")
        
        if not results['tracks']['items']:
            # Try looser search
            query = f'{title} {artist}'
            results = spotify.search(q=query, type='track', limit=10)
            print(f"\n2. Loose search: {query}")
            print(f"   Found {len(results['tracks']['items'])} results")
        
        if not results['tracks']['items']:
            print("❌ No results found")
            return
        
        # Find best match (exact copy of verification logic)
        best_match = None
        best_score = 0
        
        # Normalize input
        def normalize_title(title_input):
            if not title_input:
                return ""
            import re
            title_input = re.sub(r'^[\"\\\'\"\"``\'\'\"\"„‚]+|[\"\\\'\"\"``\'\'\"\"„‚]+$', '', title_input.strip())
            suffixes_pattern = r'\\s*[-\\(\\[]?\\s*(remaster|remastered|live|remix|acoustic|demo|single version|radio edit|explicit|deluxe|extended|instrumental|karaoke|clean|dirty|uncensored|album version|single|ep version|bonus track|\\d{4}\\s*remaster|\\d{4}|stereo|mono).*?[\\)\\]]?$'
            title_input = re.sub(suffixes_pattern, '', title_input, flags=re.IGNORECASE)
            title_input = re.sub(r'\\s*[&]\\s*', ' & ', title_input)
            title_input = re.sub(r'\\s*[+]\\s*', ' + ', title_input)
            title_input = re.sub(r'\\s+', ' ', title_input).strip()
            return title_input
        
        def normalize_artist(artist_input):
            if not artist_input:
                return ""
            import re
            artist_input = re.sub(r'^[\"\\\'\"\"]+|[\"\\\'\"\"]+$', '', artist_input.strip())
            artist_input = re.sub(r'\\s*(ft\\.|feat\\.|featuring|ft|feat)\\s+', ' feat. ', artist_input, flags=re.IGNORECASE)
            artist_input = re.sub(r'\\s+and\\s+', ' & ', artist_input, flags=re.IGNORECASE)
            artist_input = re.sub(r'\\s+', ' ', artist_input).strip()
            return artist_input
        
        norm_title = normalize_title(title).lower()
        norm_artist = normalize_artist(artist).lower()
        
        print(f"\n3. Normalized input: '{norm_title}' by '{norm_artist}'")
        
        for i, track in enumerate(results['tracks']['items']):
            if not track or not track.get('name') or not track.get('artists'):
                continue
            
            track_title = normalize_title(track['name']).lower()
            track_artist = normalize_artist(track['artists'][0]['name']).lower()
            
            print(f"\n   Track {i+1}: '{track_title}' by '{track_artist}'")
            
            # Calculate similarity score
            title_match = 1.0 if track_title == norm_title else 0.0
            
            if title_match == 0.0:
                # Handle prefix variations
                common_prefixes = ["it's ", "its ", "the ", "a ", "an "]
                title_no_prefix = norm_title
                track_no_prefix = track_title
                
                for prefix in common_prefixes:
                    if title_no_prefix.startswith(prefix):
                        title_no_prefix = title_no_prefix[len(prefix):]
                    if track_no_prefix.startswith(prefix):
                        track_no_prefix = track_no_prefix[len(prefix):]
                
                if title_no_prefix == track_no_prefix and len(title_no_prefix) > 3:
                    title_match = 0.85
                    print(f"     Title match (prefix): {title_match}")
                else:
                    print(f"     Title match: {title_match}")
            else:
                print(f"     Title match (exact): {title_match}")
            
            # Artist matching
            artist_match = 1.0 if track_artist == norm_artist else 0.0
            print(f"     Artist match: {artist_match}")
            
            # Calculate score
            score = (title_match * 0.7 + artist_match * 0.3)
            print(f"     Score: {score:.3f}")
            
            # Check threshold
            if score > best_score and score >= 0.8:
                best_score = score
                best_match = track
                print(f"     ✅ NEW BEST MATCH! (score: {score:.3f})")
            elif score >= 0.8:
                print(f"     ⚠️  Meets threshold but not better than current best ({best_score:.3f})")
            else:
                print(f"     ❌ Below threshold (0.8)")
        
        print(f"\n4. Final result:")
        if best_match:
            print(f"   ✅ Found match: '{best_match['name']}' by '{best_match['artists'][0]['name']}'")
            print(f"   Score: {best_score:.3f}")
        else:
            print(f"   ❌ No match found (best score: {best_score:.3f})")
        
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    debug_verification_step_by_step()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Test dynamic mainstream detection with real Spotify data"""

import sys
import os
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, '/home/viblio/coding_projects/music_league')

from src.music_league.dynamic_mainstream_detector import DynamicMainstreamDetector
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables
load_dotenv()

# Check if Spotify credentials are available
client_id = os.getenv('SPOTIPY_CLIENT_ID') or os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET') or os.getenv('SPOTIFY_CLIENT_SECRET')

if not client_id or not client_secret:
    print("⚠️  Spotify API credentials not found in environment")
    print("   Set SPOTIPY_CLIENT_ID/SPOTIFY_CLIENT_ID and SPOTIPY_CLIENT_SECRET/SPOTIFY_CLIENT_SECRET in .env file")
    sys.exit(1)

# Set the standard Spotipy env vars if needed
if not os.getenv('SPOTIPY_CLIENT_ID'):
    os.environ['SPOTIPY_CLIENT_ID'] = client_id
if not os.getenv('SPOTIPY_CLIENT_SECRET'):
    os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret

# Initialize Spotify client
try:
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    print("✅ Spotify client initialized\n")
except Exception as e:
    print(f"❌ Failed to initialize Spotify: {e}")
    sys.exit(1)

# Create detector
detector = DynamicMainstreamDetector(spotify_client=spotify)

# Test songs with various popularity levels
test_songs = [
    # Ultra-mainstream classics
    ("Bohemian Rhapsody", "Queen"),
    ("Gimme Shelter", "The Rolling Stones"),
    ("Stairway to Heaven", "Led Zeppelin"),
    ("Hotel California", "Eagles"),
    
    # Modern mainstream hits
    ("Flowers", "Miley Cyrus"),
    ("As It Was", "Harry Styles"),
    ("Anti-Hero", "Taylor Swift"),
    
    # Mid-tier popularity
    ("Wild Horses", "The Rolling Stones"),
    ("The Rain Song", "Led Zeppelin"),
    ("Somebody To Love", "Queen"),
    
    # Deeper cuts
    ("She's a Rainbow", "The Rolling Stones"),
    ("The Prophet's Song", "Queen"),
    ("Achilles Last Stand", "Led Zeppelin"),
    
    # Indie/alternative
    ("Motion Sickness", "Phoebe Bridgers"),
    ("Mythological Beauty", "Big Thief"),
    ("Pristine", "Snail Mail"),
]

print("=" * 80)
print("DYNAMIC MAINSTREAM DETECTION WITH SPOTIFY DATA")
print("=" * 80)
print("\nThreshold: 0.7 (scores >= 0.7 are considered mainstream)\n")

for title, artist in test_songs:
    print(f"\n🎵 {title} by {artist}")
    print("-" * 60)
    
    # Search for track on Spotify
    track_id = detector._search_track(title, artist)
    
    if track_id:
        # Get detailed information
        details = detector.get_track_details(track_id)
        
        # Calculate mainstream status
        is_mainstream, reason, score = detector.is_mainstream(
            title, artist, spotify_id=track_id, threshold=0.7
        )
        
        # Display results
        status = "🚫 MAINSTREAM" if is_mainstream else "✅ ALLOWED"
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        
        print(f"   Status: {status}")
        print(f"   Score: {score:.2f} [{bar}]")
        print(f"   Track Popularity: {details.get('popularity', 'N/A')}/100")
        print(f"   Artist Popularity: {details.get('artist_popularity', 'N/A')}/100")
        print(f"   Artist Followers: {details.get('artist_followers', 0):,}")
        print(f"   Release Date: {details.get('release_date', 'Unknown')}")
        
        if details.get('genres'):
            print(f"   Genres: {', '.join(details['genres'][:3])}")
        
        print(f"   Reason: {reason}")
        
        # Get component scores
        _, signals = detector.calculate_mainstream_score(track_id)
        if signals.get('mainstream_playlists', 0) > 0:
            print(f"   Playlist Presence: Found in {signals['mainstream_playlists']} mainstream playlists")
    else:
        print(f"   ⚠️  Could not find track on Spotify")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

# Calculate stats
mainstream_count = 0
total_tested = 0

for title, artist in test_songs:
    track_id = detector._search_track(title, artist)
    if track_id:
        is_mainstream, _, _ = detector.is_mainstream(title, artist, spotify_id=track_id)
        if is_mainstream:
            mainstream_count += 1
        total_tested += 1

print(f"\nTested {total_tested} songs found on Spotify")
print(f"Detected {mainstream_count} as mainstream")
print(f"Allowed {total_tested - mainstream_count} through filter")
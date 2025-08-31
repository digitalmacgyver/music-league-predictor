#!/usr/bin/env python3
"""Test scout's mainstream filtering with dynamic detection"""

import sys
import os

# Add project to path
sys.path.insert(0, '/home/viblio/coding_projects/music_league')
os.chdir('/home/viblio/coding_projects/music_league')

# Set up environment
from dotenv import load_dotenv
load_dotenv()

# Mock some candidates as if they came from discovery
test_candidates = [
    # Ultra mainstream - should be filtered
    {'title': 'Bohemian Rhapsody', 'artist': 'Queen', 'spotify_id': '7tFiyTwD0nx5a1eklYtX2J'},
    {'title': 'Gimme Shelter', 'artist': 'The Rolling Stones', 'spotify_id': '6H3kDe7CGoWYBabAeVWGiD'},
    {'title': 'Hotel California', 'artist': 'Eagles', 'spotify_id': '40riOy7x9W7GXjyGp4pjAv'},
    {'title': 'Shape of You', 'artist': 'Ed Sheeran', 'spotify_id': '7qiZfU4dY1lWllzX7mPBI3'},
    
    # Moderate popularity - borderline
    {'title': 'Wild Horses', 'artist': 'The Rolling Stones', 'spotify_id': '52dm9op3rbfAkc1LGXgipW'},
    {'title': 'The Rain Song', 'artist': 'Led Zeppelin', 'spotify_id': '3JLrri1xSCui3bzITDJbkk'},
    
    # Deeper cuts - should pass
    {'title': "She's a Rainbow", 'artist': 'The Rolling Stones', 'spotify_id': '6KOtheMY0KN4s9TrQHr9It'},
    {'title': "The Prophet's Song", 'artist': 'Queen', 'spotify_id': '1Ji1gZtpgMBepbNpyiLfgv'},
    {'title': 'Achilles Last Stand', 'artist': 'Led Zeppelin', 'spotify_id': '1ibHApXtb0pgplmNDRLHrJ'},
    
    # Songs without Spotify IDs (will use fallback)
    {'title': 'Some Obscure Song', 'artist': 'Unknown Artist'},
    {'title': 'Indie Track', 'artist': 'Indie Band'},
]

print("=" * 80)
print("TESTING SCOUT'S DYNAMIC MAINSTREAM FILTERING")
print("=" * 80)
print()

# Initialize scout with verbose mode
from bin.scout import SongScout
scout = SongScout(verbose=True)

print("\n" + "=" * 80)
print("FILTERING CANDIDATES")
print("=" * 80)

# Test filtering
filtered = scout._filter_mainstream_songs(test_candidates)

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)
print(f"\nInput: {len(test_candidates)} candidates")
print(f"Output: {len(filtered)} passed filter")
print(f"Filtered out: {len(test_candidates) - len(filtered)} mainstream songs")

print("\n✅ Songs that passed:")
for song in filtered:
    print(f"   • {song['title']} by {song['artist']}")

print("\n❌ Songs that were filtered:")
filtered_titles = {(s['title'], s['artist']) for s in filtered}
for song in test_candidates:
    if (song['title'], song['artist']) not in filtered_titles:
        print(f"   • {song['title']} by {song['artist']}")
#!/usr/bin/env python3
"""
Test the release date verification system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from release_date_verifier import ReleaseDateVerifier

def test_problematic_songs():
    """Test the problematic songs that were incorrectly included for 90s"""
    verifier = ReleaseDateVerifier()
    
    test_songs = [
        {"title": "True Love Waits", "artist": "Radiohead"},
        {"title": "Early in the Morning", "artist": "Gap Band"},
        {"title": "Green Onions", "artist": "Booker T. & the M.G.'s"},
        {"title": "Sunday Morning Coming Down", "artist": "Johnny Cash"},
        # Add some actual 90s songs for comparison
        {"title": "Smells Like Teen Spirit", "artist": "Nirvana"},
        {"title": "Black", "artist": "Pearl Jam"},
        {"title": "Creep", "artist": "Radiohead"}
    ]
    
    print("Testing Release Date Verification")
    print("=" * 50)
    
    target_era = "90s"
    verified_90s_songs = verifier.bulk_verify_era(test_songs, target_era)
    
    print(f"\nResults for {target_era} era:")
    print(f"Input: {len(test_songs)} songs")
    print(f"Verified as {target_era}: {len(verified_90s_songs)} songs")
    print()
    
    print("Individual Results:")
    for song in test_songs:
        is_from_era, release_year, source = verifier.verify_song_era(
            song['title'], song['artist'], target_era
        )
        
        status = "✅ VERIFIED" if is_from_era else "❌ REJECTED"
        year_info = f"({release_year})" if release_year else "(unknown)"
        print(f"{status}: {song['title']} by {song['artist']} {year_info} [{source}]")
    
    print(f"\nVerified {target_era} songs:")
    for song in verified_90s_songs:
        year = song.get('verified_release_year', 'unknown')
        source = song.get('verification_source', 'unknown')
        print(f"  • {song['title']} by {song['artist']} ({year}, {source})")

if __name__ == "__main__":
    test_problematic_songs()
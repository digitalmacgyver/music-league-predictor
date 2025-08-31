#!/usr/bin/env python3
"""
Test scout.py era filtering with the problematic songs
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from forecasting import MusicForecaster

def test_scout_era_filtering():
    """Test that the problematic songs are now filtered out by era"""
    
    # Create a forecaster instance (same as scout.py uses)
    forecaster = MusicForecaster()
    
    # Test with the problematic songs that were incorrectly included for 90s
    test_candidates = [
        {"title": "True Love Waits", "artist": "Radiohead"},
        {"title": "Early in the Morning", "artist": "Gap Band"}, 
        {"title": "Green Onions", "artist": "Booker T. & the M.G.'s"},
        {"title": "Sunday Morning Coming Down", "artist": "Johnny Cash"},
        # Add some actual 90s songs that should pass
        {"title": "Smells Like Teen Spirit", "artist": "Nirvana"},
        {"title": "Black", "artist": "Pearl Jam"},
        {"title": "Creep", "artist": "Radiohead"}
    ]
    
    print("Testing Scout.py Era Filtering Integration")
    print("=" * 50)
    print(f"Input: {len(test_candidates)} candidates")
    
    # Test era filtering (simulating what scout.py does)
    target_era = "90s"
    print(f"Target era: {target_era}")
    print()
    
    # Apply era filtering
    filtered_candidates = forecaster.filter_by_era(test_candidates, target_era)
    
    print(f"Results: {len(filtered_candidates)} candidates passed era filtering")
    print()
    
    print("Passed 90s era filtering:")
    for song in filtered_candidates:
        year = song.get('verified_release_year', 'unknown')
        source = song.get('verification_source', 'unknown')
        print(f"  ✅ {song['title']} by {song['artist']} ({year}, {source})")
    
    print()
    print("Expected results:")
    print("  ✅ Smells Like Teen Spirit by Nirvana")
    print("  ✅ Black by Pearl Jam") 
    print("  ✅ Creep by Radiohead")
    print("  ❌ True Love Waits by Radiohead (2016)")
    print("  ❌ Early in the Morning by Gap Band (1982)")
    print("  ❌ Green Onions by Booker T. & the M.G.'s (1962)")
    print("  ❌ Sunday Morning Coming Down by Johnny Cash (1972)")
    
    # Check if we got the expected results
    expected_songs = {"Smells Like Teen Spirit", "Black", "Creep"}
    actual_songs = {song['title'] for song in filtered_candidates}
    
    if expected_songs == actual_songs:
        print("\n🎉 SUCCESS: Era filtering is working correctly!")
        print(f"   - Correctly filtered out {len(test_candidates) - len(filtered_candidates)} non-90s songs")
        print(f"   - Correctly kept {len(filtered_candidates)} 90s songs")
        return True
    else:
        print(f"\n❌ FAILURE: Expected {expected_songs}, got {actual_songs}")
        return False

if __name__ == "__main__":
    success = test_scout_era_filtering()
    sys.exit(0 if success else 1)
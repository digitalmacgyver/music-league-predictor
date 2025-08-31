#!/usr/bin/env python3
"""
Test that scout.py pipeline applies era filtering correctly
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bin'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

# Import the SongScout class directly
from scout import SongScout
from forecasting import MusicForecaster

def test_scout_pipeline_era_filtering():
    """Test that era filtering is applied in the scout pipeline"""
    
    print("Testing Scout Pipeline Era Filtering")
    print("=" * 40)
    
    # Create a scout system
    scout = SongScout(verbose=True)
    
    # Create some test candidates that mix eras
    test_candidates = [
        {"title": "True Love Waits", "artist": "Radiohead", "theme_relevance": 0.8},
        {"title": "Green Onions", "artist": "Booker T. & the M.G.'s", "theme_relevance": 0.7},
        {"title": "Smells Like Teen Spirit", "artist": "Nirvana", "theme_relevance": 0.9},
        {"title": "Black", "artist": "Pearl Jam", "theme_relevance": 0.8}
    ]
    
    print(f"Input candidates: {len(test_candidates)}")
    for candidate in test_candidates:
        print(f"  • {candidate['title']} by {candidate['artist']}")
    
    # Test the forecaster's era filtering directly
    print(f"\nTesting era filtering for '90s'...")
    
    # Convert to the format expected by filter_by_era
    simple_candidates = [
        {"title": c["title"], "artist": c["artist"]} 
        for c in test_candidates
    ]
    
    filtered = scout.forecaster.filter_by_era(simple_candidates, "90s")
    
    print(f"Results: {len(filtered)} candidates passed 90s era filtering")
    for song in filtered:
        year = song.get('verified_release_year', 'unknown')
        source = song.get('verification_source', 'unknown')
        print(f"  ✅ {song['title']} by {song['artist']} ({year}, {source})")
    
    # Expected: only Nirvana and Pearl Jam should pass
    expected = {"Smells Like Teen Spirit", "Black"}
    actual = {song['title'] for song in filtered}
    
    if expected == actual:
        print("\n🎉 SUCCESS: Era filtering correctly applied in scout pipeline!")
        return True
    else:
        print(f"\n❌ FAILURE: Expected {expected}, got {actual}")
        return False

if __name__ == "__main__":
    success = test_scout_pipeline_era_filtering()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test that specific problematic songs are now being filtered correctly
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from forecasting import MusicForecaster

def test_specific_song_filtering():
    """Test that the problematic songs are now filtered correctly"""
    forecaster = MusicForecaster()
    
    # Test candidates that should be filtered (these exist in DB)
    test_candidates = [
        {"title": "One Headlight", "artist": "Wallflowers"},  # Should match "One Headlight" by "The Wallflowers" in DB
        {"title": "Green Onions", "artist": "Booker T. and the M.G.'s"},  # Should match "Booker T. & the M.G.'s" in DB
        {"title": "Test Song", "artist": "Test Artist"}  # Should NOT be filtered (doesn't exist)
    ]
    
    print("Testing specific song filtering:")
    print("=" * 50)
    
    # Test the filtering
    filtered = forecaster.filter_previous_submissions(test_candidates)
    
    print(f"Input: {len(test_candidates)} candidates")
    print(f"Output: {len(filtered)} candidates after filtering")
    print()
    
    for candidate in test_candidates:
        if candidate in filtered:
            print(f"✅ KEPT: {candidate['title']} by {candidate['artist']}")
        else:
            print(f"🚫 FILTERED: {candidate['title']} by {candidate['artist']}")
    
    # Expected: only "Test Song" should remain
    if len(filtered) == 1 and filtered[0]['title'] == "Test Song":
        print("\n🎉 SUCCESS: Filtering is working correctly!")
        return True
    else:
        print(f"\n❌ FAILURE: Expected 1 song ('Test Song'), got {len(filtered)}")
        return False

if __name__ == "__main__":
    success = test_specific_song_filtering()
    sys.exit(0 if success else 1)
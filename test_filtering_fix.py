#!/usr/bin/env python3
"""
Test script to verify the duplicate submission filtering fix
"""

from lib.nlp_text_processor import MusicTextProcessor

def test_normalization_matching():
    """Test that the normalization creates matching keys"""
    
    processor = MusicTextProcessor()
    
    # Test cases from the database vs scout.py output
    test_cases = [
        {
            "db_title": "One Headlight",
            "db_artist": "The Wallflowers",
            "candidate_title": "One Headlight", 
            "candidate_artist": "Wallflowers"
        },
        {
            "db_title": "Green Onions",
            "db_artist": "Booker T. & the M.G.'s", 
            "candidate_title": "Green Onions",
            "candidate_artist": "Booker T. and the M.G.'s"
        },
        {
            "db_title": "Sunday Morning Coming Down - Live at Ryman Auditorium, Nashville, TN - July 1970",
            "db_artist": "Johnny Cash",
            "candidate_title": "Sunday Morning Coming Down",
            "candidate_artist": "Johnny Cash" 
        }
    ]
    
    print("🔍 Testing Duplicate Filtering Normalization")
    print("=" * 60)
    
    all_passed = True
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Database: '{case['db_title']}' by '{case['db_artist']}'")
        print(f"  Candidate: '{case['candidate_title']}' by '{case['candidate_artist']}'")
        
        # Normalize database entry
        db_norm_title = processor.normalize_for_matching(case['db_title'], 'title').lower()
        db_norm_artist = processor.normalize_for_matching(case['db_artist'], 'artist').lower()
        db_key = f"{db_norm_title}|{db_norm_artist}"
        
        # Normalize candidate entry  
        cand_norm_title = processor.normalize_for_matching(case['candidate_title'], 'title').lower()
        cand_norm_artist = processor.normalize_for_matching(case['candidate_artist'], 'artist').lower()
        cand_key = f"{cand_norm_title}|{cand_norm_artist}"
        
        print(f"  DB normalized: '{db_key}'")
        print(f"  Candidate normalized: '{cand_key}'")
        
        if db_key == cand_key:
            print(f"  ✅ MATCH - Will be filtered correctly")
        else:
            print(f"  ❌ NO MATCH - Will NOT be filtered (BUG)")
            all_passed = False
    
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed!'}")
    return all_passed

if __name__ == "__main__":
    test_normalization_matching()
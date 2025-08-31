#!/usr/bin/env python3
"""
Test that legitimate music suffix removal still works after the fix
"""

from lib.nlp_text_processor import MusicTextProcessor

def test_legitimate_suffix_removal():
    """Test that we still remove legitimate music suffixes"""
    
    processor = MusicTextProcessor()
    
    # Test cases that SHOULD have suffixes removed
    test_cases = [
        ("Hotel California - Remastered", "Hotel California"),
        ("Yesterday (Live)", "Yesterday"),
        ("November Rain [Demo Version]", "November Rain"),
        ("Bohemian Rhapsody - Live at Wembley", "Bohemian Rhapsody"),
        ("Imagine (Acoustic)", "Imagine"),
        ("Come As You Are - Radio Edit", "Come As You Are"),
        ("Smells Like Teen Spirit [Explicit]", "Smells Like Teen Spirit"),
    ]
    
    print("🎵 Testing Legitimate Suffix Removal")
    print("=" * 60)
    
    all_passed = True
    for input_text, expected in test_cases:
        result = processor.normalize_for_matching(input_text, 'title')
        if result == expected:
            print(f"✅ '{input_text}' -> '{result}'")
        else:
            print(f"❌ '{input_text}' -> '{result}' (expected: '{expected}')")
            all_passed = False
    
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed!'}")

if __name__ == "__main__":
    test_legitimate_suffix_removal()
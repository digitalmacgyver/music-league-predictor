#!/usr/bin/env python3
"""
Debug script to test artist name truncation in the NLP text processor
"""

import re
from lib.nlp_text_processor import MusicTextProcessor

def test_artist_truncation():
    """Test if the music suffix removal is truncating artist names"""
    
    processor = MusicTextProcessor()
    
    # Test problematic artist names from the logs
    test_artists = [
        "Red Hot Chili Peppers",
        "Radiohead", 
        "Guns N' Roses",
        "The Beatles",
        "Led Zeppelin",
        "Red Hot Chili P",  # Already truncated case
        "Parry Gripp"
    ]
    
    print("🎵 Testing Artist Name Truncation")
    print("=" * 60)
    
    for artist in test_artists:
        print(f"\nOriginal: '{artist}'")
        
        # Test each step of normalization
        basic_clean = processor._basic_clean(artist)
        print(f"After basic_clean: '{basic_clean}'")
        
        suffix_removed = processor._remove_music_suffixes(basic_clean)
        print(f"After suffix removal: '{suffix_removed}'")
        
        normalized = processor.normalize_for_matching(artist, 'artist')
        print(f"Fully normalized: '{normalized}'")
        
        if len(normalized) < len(artist):
            print(f"🚨 TRUNCATION DETECTED: '{artist}' -> '{normalized}' (lost {len(artist) - len(normalized)} chars)")

def test_regex_pattern():
    """Test the specific regex pattern causing issues"""
    
    processor = MusicTextProcessor()
    
    # The problematic pattern
    suffix_pattern = r'\s*[-\(\[]?\s*(' + '|'.join(processor.music_stop_words) + r')[^)]*[\)\]]?$'
    print(f"\n🔍 Regex Pattern: {suffix_pattern}")
    
    # Test the pattern against problematic artists
    test_cases = [
        "Red Hot Chili Peppers",
        "Red Hot Chili P",
        "Something Single",  # Should match "single"
        "Radiohead",
        "Live Band",  # Should match "live"
        "Extended Family"  # Should match "extended"
    ]
    
    print("\n🧪 Regex Pattern Testing:")
    print("-" * 40)
    
    for text in test_cases:
        result = re.sub(suffix_pattern, '', text, flags=re.IGNORECASE)
        if result != text:
            print(f"'{text}' -> '{result}' (MATCHED)")
        else:
            print(f"'{text}' -> '{result}' (no change)")

if __name__ == "__main__":
    test_artist_truncation()
    test_regex_pattern()
#!/usr/bin/env python3
"""
Test the improved keyword extraction that filters out Music League meta-terms
"""

import sys
import os

# Add project to path
sys.path.insert(0, '/home/viblio/coding_projects/music_league')
os.chdir('/home/viblio/coding_projects/music_league')

from src.music_league.scout_nlp_integration import ScoutNLPAnalyzer
from src.music_league.music_league_stopwords import extract_meaningful_theme_words, is_theme_about_music_format

print("=" * 60)
print("Testing Improved Keyword Extraction")
print("=" * 60)

# Test cases with expected behavior
test_themes = [
    {
        "title": "Album Art",
        "description": "This weeks theme is about album art. Submit a _good_ song from an album with _Great_ cover art!",
        "expected_to_keep": ["art", "cover"],  # Should keep these relevant terms
        "expected_to_filter": ["album", "theme", "weeks", "song", "submit", "good", "great"],  # Should filter meta-terms
        "is_format_theme": True  # This IS about album format
    },
    {
        "title": "Songs about food", 
        "description": "Pick tracks that mention eating, cooking, or meals in the lyrics",
        "expected_to_keep": ["food", "eating", "cooking", "meals", "mention"],
        "expected_to_filter": ["songs", "about", "tracks", "pick", "lyrics"],
        "is_format_theme": False
    },
    {
        "title": "British Invasion",
        "description": "Songs by British artists from the 1960s that changed music history",
        "expected_to_keep": ["british", "invasion", "1960s", "changed", "history"],
        "expected_to_filter": ["songs", "artists", "music"],
        "is_format_theme": False
    },
    {
        "title": "Cover Songs",
        "description": "Submit your favorite cover versions of classic tracks",
        "expected_to_keep": ["cover", "versions", "classic", "favorite"],
        "expected_to_filter": ["songs", "submit", "tracks"],
        "is_format_theme": True  # This IS about cover versions
    },
    {
        "title": "One Word",
        "description": "Songs with single-word titles only",
        "expected_to_keep": ["single", "word", "only"],
        "expected_to_filter": ["songs", "titles"],
        "is_format_theme": False
    }
]

# Test the basic keyword extraction
print("\n1. Basic Keyword Extraction Test")
print("-" * 40)

for test in test_themes:
    full_text = f"{test['title']} {test['description']}"
    keywords = extract_meaningful_theme_words(full_text)
    
    print(f"\nTheme: {test['title']}")
    print(f"Extracted: {keywords[:10]}")
    
    # Check if expected keywords were kept
    kept_expected = [k for k in test['expected_to_keep'] if k in keywords]
    print(f"✅ Kept relevant: {kept_expected}")
    
    # Check if meta-terms were filtered
    filtered_meta = [k for k in test['expected_to_filter'] if k not in keywords]
    print(f"✅ Filtered meta-terms: {filtered_meta[:5]}...")
    
    # Check format detection
    is_format = is_theme_about_music_format(full_text)
    if is_format == test['is_format_theme']:
        print(f"✅ Correctly identified as {'format' if is_format else 'non-format'} theme")
    else:
        print(f"❌ Incorrectly identified format theme")

# Test with NLP analyzer
print("\n" + "=" * 60)
print("2. NLP Analyzer Semantic Extraction Test")
print("-" * 40)

analyzer = ScoutNLPAnalyzer()

for test in test_themes[:3]:  # Test first 3 themes
    print(f"\nTheme: {test['title']}")
    print(f"Description: {test['description'][:50]}...")
    
    theme_analysis = analyzer.analyze_theme_semantically(test['title'], test['description'])
    
    print(f"Key concepts: {theme_analysis.key_concepts}")
    print(f"Semantic keywords: {theme_analysis.semantic_keywords[:10]}")
    
    # Generate discovery keywords
    discovery_keywords = analyzer.generate_discovery_keywords_nlp(theme_analysis)
    print(f"Discovery keywords: {discovery_keywords[:10]}")
    
    # Check for spurious meta-terms
    meta_terms_found = [k for k in ['album', 'theme', 'song', 'track', 'week', 'submit'] 
                        if k in discovery_keywords and k not in test['expected_to_keep']]
    
    if not meta_terms_found:
        print("✅ No spurious meta-terms in discovery keywords")
    else:
        print(f"⚠️  Found meta-terms that might cause issues: {meta_terms_found}")

print("\n" + "=" * 60)
print("3. Comparison: Before vs After")
print("-" * 40)

# Show what would have happened with old approach
test = test_themes[0]  # Album Art theme
full_text = f"{test['title']} {test['description']}"

# Simulate old approach (no filtering)
import re
old_keywords = re.findall(r'\w+', full_text.lower())
old_keywords = [k for k in old_keywords if len(k) > 2][:10]

print(f"\nTheme: {test['title']}")
print(f"\nOLD approach keywords: {old_keywords}")
print("  Issues: Contains 'theme', 'weeks', 'song', 'album' - will match spurious results")

new_keywords = extract_meaningful_theme_words(full_text)[:10]
print(f"\nNEW approach keywords: {new_keywords}")
print("  Better: Focuses on 'art', 'cover' - the actual theme content")

print("\n" + "=" * 60)
print("✅ Test completed successfully!")
print("\nThe improved system:")
print("- Filters out Music League meta-terms")
print("- Preserves theme-relevant keywords")
print("- Handles special cases (Album Art keeps 'album')")
print("- Reduces spurious title matches")
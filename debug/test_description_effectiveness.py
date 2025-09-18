#!/usr/bin/env python3
"""Test the effectiveness of the --description option"""

import sys
import os
import json

# Add project to path
sys.path.insert(0, '/home/viblio/coding_projects/music_league')
os.chdir('/home/viblio/coding_projects/music_league')

from dotenv import load_dotenv
load_dotenv()

# Import components
from bin.scout import SongScout
from src.music_league.forecasting import MusicForecaster

# Test cases: same theme with different descriptions
test_cases = [
    {
        "theme": "Night",
        "description": "",
        "label": "No description"
    },
    {
        "theme": "Night",
        "description": "Songs about nighttime, darkness, or things that happen after dark",
        "label": "Basic description"
    },
    {
        "theme": "Night",
        "description": "Songs that capture the feeling of being awake at 3am - could be partying, insomnia, late night drives, or contemplative solitude",
        "label": "Specific mood description"
    },
    {
        "theme": "Night",
        "description": "Upbeat dance songs about nightlife and partying",
        "label": "Genre-specific description"
    }
]

print("=" * 80)
print("TESTING DESCRIPTION EFFECTIVENESS")
print("=" * 80)
print("\nWe'll test the same theme 'Night' with different descriptions\n")

# Initialize components
forecaster = MusicForecaster(verbose=False)
scout = SongScout(verbose=False)

for test in test_cases:
    print("-" * 80)
    print(f"TEST: {test['label']}")
    print(f"Theme: '{test['theme']}'")
    if test['description']:
        print(f"Description: '{test['description']}'")
    else:
        print("Description: (none)")
    print("-" * 80)
    
    # 1. Test theme analysis
    print("\n📊 THEME ANALYSIS:")
    theme_analysis = forecaster.analyze_theme_with_llm(test['theme'], test['description'])
    
    if theme_analysis:
        print(f"  Emotional Tone: {theme_analysis.emotional_tone}")
        print(f"  Energy Level: {theme_analysis.energy_level}")
        print(f"  Keywords: {', '.join(theme_analysis.thematic_keywords[:5])}")
        print(f"  Genres: {', '.join(theme_analysis.genre_preferences[:3])}")
    
    # 2. Test keyword extraction
    print("\n🔍 KEYWORD EXTRACTION:")
    keywords = scout._extract_theme_keywords_with_llm(test['theme'], test['description'])
    print(f"  Generated keywords: {', '.join(keywords[:8])}")
    
    # 3. Test candidate discovery (small sample)
    print("\n🎵 SAMPLE CANDIDATES (first 5):")
    
    # Just get a few candidates from LLM discovery
    llm_candidates = scout._discover_via_llm_knowledge(test['theme'], test['description'], 5)
    
    if llm_candidates:
        for i, candidate in enumerate(llm_candidates[:5], 1):
            print(f"  {i}. {candidate['title']} by {candidate['artist']}")
            if 'reasoning' in candidate:
                print(f"     Reasoning: {candidate['reasoning'][:100]}...")
    else:
        print("  (No candidates generated)")
    
    print()

print("=" * 80)
print("ANALYSIS SUMMARY")
print("=" * 80)

print("""
The description parameter affects:

1. **Theme Analysis**: More specific descriptions lead to more targeted emotional 
   tone and genre preferences in the LLM's understanding.

2. **Keyword Generation**: Descriptions add contextual keywords that wouldn't be 
   extracted from the theme alone.

3. **Candidate Discovery**: Descriptions guide the LLM to suggest songs that match 
   the specific interpretation rather than all possible interpretations.

4. **Search Queries**: Descriptions are concatenated with themes for Spotify and 
   playlist searches, affecting what results are found.

5. **Historical Matching**: Descriptions are searched in past round descriptions 
   to find similar themes that performed well.
""")
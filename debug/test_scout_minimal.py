#!/usr/bin/env python3
"""Minimal test of scout functionality"""

import sys
import os
import logging

# Setup logging to see errors
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add project to path
sys.path.insert(0, '/home/viblio/coding_projects/music_league')
os.chdir('/home/viblio/coding_projects/music_league')

from dotenv import load_dotenv
load_dotenv()

print("Testing minimal scout functionality...")

from bin.scout import SongScout

# Create scout with minimal features
scout = SongScout(
    verbose=True,
    enable_lyrics_discovery=False,
    enable_playlist_discovery=False
)

print("\nTesting theme analysis...")

# Test theme analysis (this is what was failing)
try:
    from src.music_league.forecasting import MusicForecaster
    forecaster = MusicForecaster(verbose=False)
    
    # This should work now
    theme_analysis = forecaster.analyze_theme_with_llm(
        "Album Art", 
        "This weeks theme is about album art"
    )
    print(f"✅ Theme analysis succeeded: {theme_analysis.emotional_tone if theme_analysis else 'None'}")
except Exception as e:
    print(f"❌ Theme analysis failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting minimal discovery...")

# Try minimal candidate discovery
try:
    candidates = scout.discover_candidates(
        theme="Test Theme",
        description="Test description",
        target_count=1
    )
    print(f"✅ Discovery succeeded: {len(candidates)} candidates found")
except Exception as e:
    print(f"❌ Discovery failed: {e}")
    import traceback
    traceback.print_exc()

scout.close()
print("\n✅ Test completed")
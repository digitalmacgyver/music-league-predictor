#!/usr/bin/env ./venv/bin/python3
"""
Debug script to identify where Scout is hanging
"""

import sys
import signal
import traceback
from scout import SongScout

def timeout_handler(signum, frame):
    print("\n⏰ TIMEOUT! Here's where we were stuck:")
    traceback.print_stack(frame)
    sys.exit(1)

# Set a 10 second timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)

print("Creating Scout instance...")
scout = SongScout(
    verbose=True, 
    enable_voter_preferences=False,
    enable_historical_patterns=False,
    enable_ensemble_models=False,
    use_legacy_scoring=True,
    enable_lyrics_discovery=False,
    enable_playlist_discovery=False
)
print("✅ Scout created successfully")

print("\nTrying to discover candidates...")
try:
    candidates = scout.discover_candidates(
        theme="Songs about colors",
        target_count=5
    )
    print(f"✅ Found {len(candidates)} candidates")
    for c in candidates[:3]:
        print(f"  - {c.get('title', 'Unknown')} by {c.get('artist', 'Unknown')}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

signal.alarm(0)  # Cancel the alarm
print("\n✅ Test completed without hanging")
#!/usr/bin/env python3
"""Debug script to test individual discovery methods"""

import sys
import os
import time

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

from scout import SongScout

print("Creating scout instance (no historical patterns to speed up)...")
scout = SongScout(verbose=True, enable_historical_patterns=False, 
                  enable_lyrics_discovery=False, enable_playlist_discovery=False)
print("Scout created!\n")

theme = "Songs about Food"
description = ""

# Test each discovery method individually
methods = [
    ('_find_historical_matches', (theme, description)),
    ('_discover_by_keywords', (theme, description, None, None)),
    ('_discover_via_spotify', (theme, description, 10)),
]

for method_name, args in methods:
    if hasattr(scout, method_name):
        print(f"\n{'='*50}")
        print(f"Testing {method_name}...")
        try:
            start = time.time()
            method = getattr(scout, method_name)
            result = method(*args)
            elapsed = time.time() - start
            print(f"✅ {method_name} returned {len(result)} candidates in {elapsed:.2f}s")
        except Exception as e:
            print(f"❌ {method_name} failed: {e}")
    else:
        print(f"⚠️  Method {method_name} not found")

# Now test the problematic LLM discovery
print(f"\n{'='*50}")
print("Testing _discover_via_llm_knowledge (this might hang)...")
try:
    start = time.time()
    result = scout._discover_via_llm_knowledge(theme, description, 10)
    elapsed = time.time() - start
    print(f"✅ _discover_via_llm_knowledge returned {len(result)} candidates in {elapsed:.2f}s")
except Exception as e:
    print(f"❌ _discover_via_llm_knowledge failed: {e}")

scout.close()
print("\nDone!")
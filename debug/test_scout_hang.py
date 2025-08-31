#!/usr/bin/env python3
"""Debug script to find where scout.py is hanging"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

print("1. Importing modules...")
from scout import SongScout
print("2. Creating scout instance...")
scout = SongScout(verbose=True, enable_historical_patterns=False)
print("3. Scout created successfully!")

print("4. Testing discover_songs method...")
theme = "Songs about Food"
description = ""

# Test the discover_candidates method
print(f"5. Calling discover_candidates('{theme}')...")
candidates = scout.discover_candidates(theme, description)
print(f"6. discover_candidates returned {len(candidates)} candidates")

scout.close()
print("7. Done!")
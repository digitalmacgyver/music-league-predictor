#!/usr/bin/env python3
"""Test the enhanced mainstream filtering"""

import sys
sys.path.insert(0, '/home/viblio/coding_projects/music_league')

from src.music_league.mainstream_detector import MainstreamDetector

# Create detector
detector = MainstreamDetector()

# Test songs that SHOULD be filtered
mainstream_songs = [
    ("Gimme Shelter", "The Rolling Stones"),
    ("Gimmie Shelter", "Rolling Stones"),  # Typo
    ("Paint It Black", "The Rolling Stones"),
    ("(I Can't Get No) Satisfaction", "The Rolling Stones"),
    ("Bohemian Rhapsody", "Queen"),
    ("Stairway to Heaven", "Led Zeppelin"),
    ("Hotel California", "Eagles"),
    ("Sweet Child O' Mine", "Guns N' Roses"),
    ("Hey Jude", "The Beatles"),
    ("Shape of You", "Ed Sheeran"),
    ("Blinding Lights", "The Weeknd"),
]

# Test songs that should NOT be filtered (deeper cuts)
deeper_cuts = [
    ("Mother's Little Helper", "The Rolling Stones"),
    ("She's a Rainbow", "The Rolling Stones"),
    ("2000 Light Years From Home", "The Rolling Stones"),
    ("The Rain Song", "Led Zeppelin"),
    ("Achilles Last Stand", "Led Zeppelin"),
    ("The Prophet's Song", "Queen"),
    ("'39", "Queen"),
    ("Blue Jay Way", "The Beatles"),
    ("Tomorrow Never Knows", "The Beatles"),
]

print("=" * 70)
print("MAINSTREAM SONGS (should be filtered):")
print("=" * 70)
filtered_count = 0
for title, artist in mainstream_songs:
    is_mainstream, reason = detector.is_mainstream(title, artist)
    if is_mainstream:
        print(f"✅ FILTERED: {title} by {artist}")
        print(f"   Reason: {reason}")
        filtered_count += 1
    else:
        print(f"❌ MISSED: {title} by {artist} - NOT FILTERED!")

print(f"\nFiltered {filtered_count}/{len(mainstream_songs)} mainstream songs")

print("\n" + "=" * 70)
print("DEEPER CUTS (should NOT be filtered):")
print("=" * 70)
passed_count = 0
for title, artist in deeper_cuts:
    is_mainstream, reason = detector.is_mainstream(title, artist)
    if not is_mainstream:
        print(f"✅ PASSED: {title} by {artist}")
        passed_count += 1
    else:
        print(f"❌ BLOCKED: {title} by {artist}")
        print(f"   Reason: {reason}")

print(f"\nAllowed {passed_count}/{len(deeper_cuts)} deeper cuts through")

# Test mainstream scores
print("\n" + "=" * 70)
print("MAINSTREAM SCORES (0.0 = obscure, 1.0 = ultra-mainstream):")
print("=" * 70)

test_scores = [
    ("Gimme Shelter", "The Rolling Stones"),
    ("Wild Horses", "The Rolling Stones"),
    ("She's a Rainbow", "The Rolling Stones"),
    ("Some B-side", "The Rolling Stones"),
    ("Bohemian Rhapsody", "Queen"),
    ("The Prophet's Song", "Queen"),
    ("Hey Jude", "The Beatles"),
    ("Blue Jay Way", "The Beatles"),
    ("Random Indie Song", "Unknown Artist"),
]

for title, artist in test_scores:
    score = detector.get_mainstream_score(title, artist)
    bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
    print(f"{score:.2f} [{bar}] {title} by {artist}")
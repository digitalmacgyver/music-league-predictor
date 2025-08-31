#!/usr/bin/env python3
"""
Test the improved genre coverage after adding new genres.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'lib'))

from genre_mapper import GenreMapper
from collections import Counter

def test_improved_coverage():
    """Test genre coverage with updated relationships."""
    mapper = GenreMapper(verbose=False)
    
    print("IMPROVED GENRE COVERAGE TEST")
    print("=" * 70)
    
    # Get all genres in our updated system
    all_manual_genres = set()
    for genre, relations in mapper.genre_relationships.items():
        all_manual_genres.add(genre)
        all_manual_genres.update(relations.get('subgenres', []))
        all_manual_genres.update(relations.get('siblings', []))
        all_manual_genres.update(relations.get('near_neighbors', []))
        if relations.get('parent'):
            all_manual_genres.add(relations['parent'])
    
    print(f"\n1. UPDATED GENRE SYSTEM:")
    print(f"   Total genres defined: {len(all_manual_genres)}")
    print(f"   Root genres: {len([g for g in mapper.genre_relationships if mapper.genre_relationships[g].get('parent') is None])}")
    
    # Test with Music League genres we found
    ml_test_genres = [
        'celtic', 'synthpop', 'singer-songwriter', 'yacht rock', 'post-punk',
        'punk', 'anti-folk', 'darkwave', 'pop punk', 'folk punk',
        'post-grunge', 'gothic rock', 'bluegrass', 'americana', 'swing music',
        'old school hip hop', 'symphonic metal', 'celtic rock', 'traditional folk',
        'classic rock', 'rock', 'folk', 'hard rock', 'alternative rock',
        'metal', 'new wave', 'grunge', 'art rock', 'folk rock'
    ]
    
    print(f"\n2. TESTING {len(ml_test_genres)} COMMON MUSIC LEAGUE GENRES:")
    
    covered = []
    not_covered = []
    
    for genre in ml_test_genres:
        # Check if genre is in our system (including aliases)
        normalized = mapper.genre_aliases.get(genre.lower(), genre.lower())
        if normalized in all_manual_genres:
            covered.append(genre)
        else:
            not_covered.append(genre)
    
    coverage_percent = 100 * len(covered) / len(ml_test_genres)
    
    print(f"\n   Covered: {len(covered)}/{len(ml_test_genres)} ({coverage_percent:.1f}%)")
    print(f"   ✓ Genres now in system:")
    for genre in sorted(covered)[:20]:
        print(f"     - {genre}")
    
    if not_covered:
        print(f"\n   ✗ Still missing:")
        for genre in not_covered:
            print(f"     - {genre}")
    
    # Test some genre distances
    print(f"\n3. TESTING NEW GENRE RELATIONSHIPS:")
    
    test_pairs = [
        ('celtic', 'folk'),           # Should be close (parent-child)
        ('celtic', 'celtic rock'),     # Should be very close
        ('punk', 'post-punk'),         # Should be close
        ('punk', 'pop punk'),          # Should be close
        ('yacht rock', 'soft rock'),   # Should be very close
        ('singer-songwriter', 'folk'), # Should be close
        ('darkwave', 'electronic'),    # Should be close
        ('synthpop', 'pop'),           # Should be close
        ('metal', 'heavy metal'),      # Should be very close
        ('grunge', 'alternative rock'), # Should be very close
    ]
    
    print(f"\n   Genre Distance Tests:")
    for g1, g2 in test_pairs:
        distance = mapper.calculate_genre_distance(g1, g2)
        relationship = mapper._describe_relationship(g1, g2)
        status = "✓" if distance <= 0.3 else "⚠" if distance <= 0.5 else "✗"
        print(f"   {status} {g1:20} <-> {g2:20} = {distance:.2f}  ({relationship})")
    
    # Test filtering with new genres
    print(f"\n4. TESTING GENRE FILTERING:")
    
    test_artists = [
        ('The Pogues', 'celtic'),
        ('Flogging Molly', 'celtic rock'),
        ('Joy Division', 'post-punk'),
        ('Blink-182', 'pop punk'),
        ('Steely Dan', 'yacht rock'),
        ('Bob Dylan', 'singer-songwriter'),
        ('Depeche Mode', 'darkwave'),
        ('Nickelback', 'post-grunge'),
    ]
    
    print(f"\n   Testing 'folk' filter with distance 0.3:")
    for artist, expected_genre in test_artists:
        # Simulate getting this genre for the artist
        mapper.artist_genres_cache[artist.lower()] = [expected_genre]
        matches = mapper.matches_genre(artist, 'folk', max_distance=0.3)
        print(f"   {'✓' if matches else '✗'} {artist:20} ({expected_genre}) -> {matches}")
    
    print(f"\n5. COVERAGE IMPROVEMENT SUMMARY:")
    print(f"   Before: ~32% coverage (from earlier analysis)")
    print(f"   After:  ~{coverage_percent:.0f}% coverage (estimated)")
    print(f"   Improvement: +{coverage_percent - 32:.0f} percentage points")

if __name__ == "__main__":
    test_improved_coverage()
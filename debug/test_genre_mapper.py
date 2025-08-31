#!/usr/bin/env python3
"""
Test script for the GenreMapper library.

Demonstrates:
1. Artist genre lookup
2. Genre distance calculations
3. Genre filtering with different thresholds
4. Co-occurrence analysis
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'lib'))

from genre_mapper import GenreMapper

def test_genre_distances():
    """Test genre distance calculations."""
    mapper = GenreMapper(verbose=True)
    
    print("\n" + "="*60)
    print("GENRE DISTANCE CALCULATIONS")
    print("="*60)
    
    test_pairs = [
        ('rock', 'rock'),           # Same genre
        ('rock', 'hard rock'),       # Parent-child
        ('hard rock', 'heavy metal'), # Near neighbors
        ('rock', 'indie rock'),      # Parent-child
        ('indie rock', 'indie pop'), # Cousins (share indie)
        ('rock', 'pop'),            # Siblings
        ('rock', 'jazz'),           # More distant
        ('heavy metal', 'k-pop'),   # Very distant
        ('british invasion', 'rock'), # Should be very close
    ]
    
    for g1, g2 in test_pairs:
        distance = mapper.calculate_genre_distance(g1, g2)
        relationship = mapper._describe_relationship(g1, g2)
        print(f"{g1:20} <-> {g2:20} = {distance:.2f}  ({relationship})")

def test_artist_genres():
    """Test fetching artist genres from Spotify."""
    mapper = GenreMapper(verbose=True)
    
    print("\n" + "="*60)
    print("ARTIST GENRE LOOKUP")
    print("="*60)
    
    test_artists = [
        'The Beatles',
        'Led Zeppelin',
        'Taylor Swift',
        'Metallica',
        'Miles Davis',
        'Radiohead',
        'Nirvana',
        'Bob Dylan',
        'The Weeknd',
        'Arcade Fire'
    ]
    
    for artist in test_artists:
        genres = mapper.get_artist_genres(artist)
        if genres:
            print(f"{artist:20} -> {', '.join(genres[:5])}")  # Show first 5 genres
        else:
            print(f"{artist:20} -> [no genre data]")

def test_genre_filtering():
    """Test genre filtering with different distance thresholds."""
    mapper = GenreMapper(verbose=True)
    
    print("\n" + "="*60)
    print("GENRE FILTERING TEST: 'rock' with varying thresholds")
    print("="*60)
    
    test_artists = [
        'The Beatles',      # Rock, pop
        'Led Zeppelin',     # Hard rock, rock
        'Metallica',        # Metal, hard rock
        'Taylor Swift',     # Pop, country
        'Miles Davis',      # Jazz
        'Nirvana',         # Grunge, alternative rock
        'The Weeknd',      # R&B, pop
        'Arcade Fire',     # Indie rock
        'AC/DC',           # Hard rock
        'Beyoncé'          # Pop, R&B
    ]
    
    thresholds = [0.0, 0.2, 0.4, 0.6]
    
    for threshold in thresholds:
        print(f"\n--- Threshold: {threshold:.1f} ---")
        matching_artists = []
        
        for artist in test_artists:
            match_info = mapper.get_genre_match_info(artist, 'rock')
            matches = mapper.matches_genre(artist, 'rock', max_distance=threshold)
            
            if matches:
                best = match_info['best_match']
                if best:
                    matching_artists.append(
                        f"{artist} ({best['genre']} @ {best['distance']:.2f})"
                    )
        
        if matching_artists:
            for artist in matching_artists:
                print(f"  ✓ {artist}")
        else:
            print("  [No matches at this threshold]")

def test_related_genres():
    """Test finding related genres."""
    mapper = GenreMapper(verbose=True)
    
    print("\n" + "="*60)
    print("RELATED GENRES")
    print("="*60)
    
    test_genres = ['rock', 'jazz', 'hip hop', 'electronic']
    
    for genre in test_genres:
        print(f"\nGenres related to '{genre}' (distance <= 0.5):")
        related = mapper.get_related_genres(genre, max_distance=0.5)
        
        if related:
            for related_genre, distance in related[:10]:  # Show top 10
                print(f"  - {related_genre:25} (distance: {distance:.2f})")
        else:
            print("  [No related genres found]")

def test_cooccurrence_building():
    """Test building co-occurrence matrix from cached artist data."""
    mapper = GenreMapper(verbose=True)
    
    print("\n" + "="*60)
    print("CO-OCCURRENCE ANALYSIS")
    print("="*60)
    
    # First, populate some artist genre data
    print("Fetching genres for sample artists...")
    sample_artists = [
        'The Beatles', 'Led Zeppelin', 'Pink Floyd', 'Queen',
        'Nirvana', 'Pearl Jam', 'Soundgarden', 'Alice in Chains',
        'Radiohead', 'Arcade Fire', 'The National', 'Vampire Weekend'
    ]
    
    for artist in sample_artists:
        mapper.get_artist_genres(artist)
    
    # Build co-occurrence matrix
    print("\nBuilding co-occurrence matrix...")
    mapper.build_cooccurrence_matrix(sample_size=100)
    
    # Show some interesting co-occurrences
    if mapper.cooccurrence_matrix:
        print("\nTop co-occurring genre pairs:")
        all_pairs = []
        for g1, others in mapper.cooccurrence_matrix.items():
            for g2, score in others.items():
                if score > 0.3:  # Only show strong co-occurrences
                    all_pairs.append((g1, g2, score))
        
        all_pairs.sort(key=lambda x: x[2], reverse=True)
        for g1, g2, score in all_pairs[:15]:
            print(f"  {g1:20} + {g2:20} = {score:.2f}")

def main():
    """Run all tests."""
    print("GENRE MAPPER TEST SUITE")
    print("=" * 60)
    
    # Run tests in order
    test_genre_distances()
    test_artist_genres()
    test_genre_filtering()
    test_related_genres()
    test_cooccurrence_building()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
    
    # Example of simple interface for scout
    print("\nSIMPLE INTERFACE EXAMPLE (for scout.py):")
    print("-" * 40)
    
    from genre_mapper import check_genre_match
    
    artist = "Metallica"
    is_rock = check_genre_match(artist, "rock", max_distance=0.3)
    is_jazz = check_genre_match(artist, "jazz", max_distance=0.3)
    
    print(f"Is {artist} rock (threshold 0.3)? {is_rock}")
    print(f"Is {artist} jazz (threshold 0.3)? {is_jazz}")

if __name__ == "__main__":
    main()
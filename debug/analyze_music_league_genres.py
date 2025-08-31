#!/usr/bin/env python3
"""
Analyze genre coverage for artists in the Music League database.
Fetches genres for all unique artists and compares with our genre mapper.
"""

import sys
import sqlite3
import time
from pathlib import Path
from collections import Counter
sys.path.append(str(Path(__file__).parent.parent / 'lib'))

from genre_mapper import GenreMapper

def get_music_league_artists():
    """Get all unique artists from Music League database."""
    db_path = Path('data/music_league.db')
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get unique artists from songs table
    cursor.execute("""
        SELECT DISTINCT artist
        FROM songs
        WHERE artist IS NOT NULL AND artist != ''
        ORDER BY artist
    """)
    
    artists = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return artists

def analyze_genre_coverage():
    """Analyze genre coverage for Music League artists."""
    print("MUSIC LEAGUE GENRE COVERAGE ANALYSIS")
    print("=" * 70)
    
    # Get all Music League artists
    ml_artists = get_music_league_artists()
    print(f"\n1. MUSIC LEAGUE DATABASE:")
    print(f"   Total unique artists: {len(ml_artists)}")
    
    # Initialize genre mapper
    mapper = GenreMapper(verbose=False)
    
    # Get genres that are already in our system
    existing_manual_genres = set()
    for genre, relations in mapper.genre_relationships.items():
        existing_manual_genres.add(genre)
        existing_manual_genres.update(relations.get('subgenres', []))
        existing_manual_genres.update(relations.get('siblings', []))
        existing_manual_genres.update(relations.get('near_neighbors', []))
        if relations.get('parent'):
            existing_manual_genres.add(relations['parent'])
    
    print(f"\n2. FETCHING SPOTIFY GENRES FOR MUSIC LEAGUE ARTISTS:")
    print(f"   Processing {len(ml_artists)} artists...")
    print(f"   (This may take a while due to API rate limits)")
    
    # Track all genres found
    all_ml_genres = Counter()
    artists_with_genres = 0
    artists_without_genres = []
    
    # Process in batches to show progress
    batch_size = 50
    for i in range(0, len(ml_artists), batch_size):
        batch = ml_artists[i:i+batch_size]
        print(f"   Processing artists {i+1}-{min(i+batch_size, len(ml_artists))}...")
        
        for artist in batch:
            genres = mapper.get_artist_genres(artist)
            if genres:
                artists_with_genres += 1
                for genre in genres:
                    all_ml_genres[genre] += 1
            else:
                artists_without_genres.append(artist)
            
            # Small delay to be nice to Spotify API
            time.sleep(0.1)
    
    print(f"\n3. GENRE COVERAGE RESULTS:")
    print(f"   Artists with genre data: {artists_with_genres}/{len(ml_artists)} ({100*artists_with_genres/len(ml_artists):.1f}%)")
    print(f"   Artists without genre data: {len(artists_without_genres)}")
    print(f"   Total unique genres discovered: {len(all_ml_genres)}")
    
    # Find new genres not in our manual relationships
    ml_genre_set = set(all_ml_genres.keys())
    new_genres = ml_genre_set - existing_manual_genres
    
    print(f"\n4. NEW GENRES DISCOVERED (not in our manual hierarchy):")
    print(f"   Found {len(new_genres)} new genres")
    
    if new_genres:
        # Sort by frequency in Music League
        new_genres_with_count = [(g, all_ml_genres[g]) for g in new_genres]
        new_genres_with_count.sort(key=lambda x: x[1], reverse=True)
        
        print("\n   Top 30 new genres by frequency:")
        for genre, count in new_genres_with_count[:30]:
            print(f"   - {genre:40} ({count} artists)")
    
    # Find manual genres that don't appear in Music League
    unused_manual_genres = existing_manual_genres - ml_genre_set
    
    print(f"\n5. UNUSED MANUAL GENRES (defined but not in Music League):")
    print(f"   Found {len(unused_manual_genres)} unused genres")
    
    if unused_manual_genres:
        print("\n   Genres we defined but haven't seen:")
        for genre in sorted(unused_manual_genres)[:30]:
            print(f"   - {genre}")
    
    # Show most common Music League genres
    print(f"\n6. MOST COMMON GENRES IN MUSIC LEAGUE:")
    for genre, count in all_ml_genres.most_common(30):
        in_manual = "✓" if genre in existing_manual_genres else "✗"
        print(f"   {in_manual} {genre:40} ({count} artists)")
    
    # Sample of artists without genres (might need manual mapping)
    print(f"\n7. SAMPLE ARTISTS WITHOUT GENRE DATA:")
    if artists_without_genres:
        print("   These artists might need manual genre assignment or are too obscure:")
        for artist in artists_without_genres[:20]:
            print(f"   - {artist}")
    
    # Calculate coverage statistics
    print(f"\n8. COVERAGE STATISTICS:")
    
    # How many ML genres are in our system?
    covered_genres = ml_genre_set & existing_manual_genres
    print(f"   Genres in both systems: {len(covered_genres)}/{len(ml_genre_set)} ({100*len(covered_genres)/len(ml_genre_set):.1f}%)")
    
    # Weight by frequency
    covered_artist_count = sum(all_ml_genres[g] for g in covered_genres)
    total_artist_count = sum(all_ml_genres.values())
    print(f"   Artist-genre pairs covered: {covered_artist_count}/{total_artist_count} ({100*covered_artist_count/total_artist_count:.1f}%)")
    
    # Recommendations
    print(f"\n9. RECOMMENDATIONS:")
    
    important_missing = []
    for genre, count in new_genres_with_count[:10]:
        if count >= 5:  # Appears in at least 5 artists
            important_missing.append((genre, count))
    
    if important_missing:
        print("\n   High-priority genres to add (frequent in Music League):")
        for genre, count in important_missing:
            print(f"   - {genre:40} ({count} artists)")
            # Suggest parent genre
            if 'rock' in genre.lower():
                print(f"     → Suggested parent: rock")
            elif 'pop' in genre.lower():
                print(f"     → Suggested parent: pop")
            elif 'metal' in genre.lower():
                print(f"     → Suggested parent: heavy metal")
            elif 'jazz' in genre.lower():
                print(f"     → Suggested parent: jazz")
            elif 'electronic' in genre.lower() or 'edm' in genre.lower():
                print(f"     → Suggested parent: electronic")
            elif 'folk' in genre.lower():
                print(f"     → Suggested parent: folk")
            elif 'indie' in genre.lower():
                print(f"     → Suggested parent: indie rock or indie pop")
    
    return {
        'ml_artists': len(ml_artists),
        'artists_with_genres': artists_with_genres,
        'total_genres': len(all_ml_genres),
        'new_genres': new_genres,
        'unused_manual_genres': unused_manual_genres,
        'coverage_percent': 100 * covered_artist_count / total_artist_count if total_artist_count > 0 else 0
    }

if __name__ == "__main__":
    results = analyze_genre_coverage()
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print(f"Overall genre coverage: {results['coverage_percent']:.1f}%")
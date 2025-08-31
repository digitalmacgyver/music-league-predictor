#!/usr/bin/env python3
"""
Fast analysis of genre coverage for Music League artists.
Uses cached data and samples for efficiency.
"""

import sys
import sqlite3
import json
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
    
    # Get unique artists with their frequency
    cursor.execute("""
        SELECT artist, COUNT(*) as song_count
        FROM songs
        WHERE artist IS NOT NULL AND artist != ''
        GROUP BY LOWER(artist)
        ORDER BY song_count DESC
    """)
    
    artists = [(row[0], row[1]) for row in cursor.fetchall()]
    conn.close()
    
    return artists

def analyze_cached_genres():
    """Analyze genres using cached data."""
    print("MUSIC LEAGUE GENRE COVERAGE ANALYSIS (FAST)")
    print("=" * 70)
    
    # Get all Music League artists
    ml_artists = get_music_league_artists()
    print(f"\n1. MUSIC LEAGUE DATABASE:")
    print(f"   Total unique artists: {len(ml_artists)}")
    print(f"   Top artists by frequency:")
    for artist, count in ml_artists[:10]:
        print(f"   - {artist:30} ({count} songs)")
    
    # Initialize genre mapper and use existing cache
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
    
    print(f"\n2. ANALYZING CACHED GENRE DATA:")
    print(f"   Artists already in cache: {len(mapper.artist_genres_cache)}")
    
    # Track all genres found
    all_ml_genres = Counter()
    artists_with_genres = 0
    artists_without_genres = []
    cached_artists = 0
    sample_new_artists = []
    
    # Check which ML artists are in cache
    for artist, song_count in ml_artists:
        artist_lower = artist.lower()
        if artist_lower in mapper.artist_genres_cache:
            cached_artists += 1
            genres = mapper.artist_genres_cache[artist_lower]
            if genres:
                artists_with_genres += 1
                for genre in genres:
                    all_ml_genres[genre] += 1
            else:
                artists_without_genres.append(artist)
        else:
            sample_new_artists.append(artist)
    
    print(f"   ML artists in cache: {cached_artists}/{len(ml_artists)} ({100*cached_artists/len(ml_artists):.1f}%)")
    
    # Fetch genres for a small sample of uncached artists
    print(f"\n3. SAMPLING UNCACHED ARTISTS:")
    sample_size = min(50, len(sample_new_artists))
    print(f"   Fetching genres for {sample_size} uncached artists...")
    
    for artist in sample_new_artists[:sample_size]:
        genres = mapper.get_artist_genres(artist)
        if genres:
            artists_with_genres += 1
            for genre in genres:
                all_ml_genres[genre] += 1
        else:
            artists_without_genres.append(artist)
    
    # Extrapolate coverage
    total_sampled = cached_artists + sample_size
    coverage_rate = artists_with_genres / total_sampled if total_sampled > 0 else 0
    
    print(f"\n4. GENRE COVERAGE RESULTS:")
    print(f"   Artists analyzed: {total_sampled}")
    print(f"   Artists with genre data: {artists_with_genres} ({100*coverage_rate:.1f}%)")
    print(f"   Estimated total coverage: ~{int(coverage_rate * len(ml_artists))} artists")
    print(f"   Total unique genres discovered: {len(all_ml_genres)}")
    
    # Find new genres not in our manual relationships
    ml_genre_set = set(all_ml_genres.keys())
    new_genres = ml_genre_set - existing_manual_genres
    
    print(f"\n5. NEW GENRES DISCOVERED (not in our manual hierarchy):")
    print(f"   Found {len(new_genres)} new genres")
    
    if new_genres:
        # Sort by frequency
        new_genres_with_count = [(g, all_ml_genres[g]) for g in new_genres]
        new_genres_with_count.sort(key=lambda x: x[1], reverse=True)
        
        print("\n   Top new genres by frequency:")
        for genre, count in new_genres_with_count[:25]:
            print(f"   - {genre:40} ({count} artists)")
    
    # Find manual genres that don't appear in Music League
    unused_manual_genres = existing_manual_genres - ml_genre_set
    
    print(f"\n6. UNUSED MANUAL GENRES (defined but not in Music League):")
    print(f"   Found {len(unused_manual_genres)} unused genres")
    
    if unused_manual_genres:
        print("\n   Genres we defined but haven't seen (first 25):")
        for genre in sorted(unused_manual_genres)[:25]:
            print(f"   - {genre}")
    
    # Show most common Music League genres
    print(f"\n7. MOST COMMON GENRES IN MUSIC LEAGUE:")
    print(f"   {'In System':10} Genre")
    print(f"   {'-'*10} {'-'*50}")
    for genre, count in all_ml_genres.most_common(30):
        in_manual = "✓" if genre in existing_manual_genres else "✗"
        print(f"   {in_manual:^10} {genre:40} ({count} artists)")
    
    # Sample of artists without genres
    print(f"\n8. SAMPLE ARTISTS WITHOUT GENRE DATA:")
    if artists_without_genres:
        print("   These artists might be too obscure or misspelled:")
        for artist in artists_without_genres[:15]:
            print(f"   - {artist}")
    
    # Calculate coverage statistics
    print(f"\n9. COVERAGE STATISTICS:")
    
    # How many ML genres are in our system?
    covered_genres = ml_genre_set & existing_manual_genres
    print(f"   Genres in both systems: {len(covered_genres)}/{len(ml_genre_set)} ({100*len(covered_genres)/len(ml_genre_set) if ml_genre_set else 0:.1f}%)")
    
    # Weight by frequency
    covered_artist_count = sum(all_ml_genres[g] for g in covered_genres)
    total_artist_count = sum(all_ml_genres.values())
    print(f"   Artist-genre pairs covered: {covered_artist_count}/{total_artist_count} ({100*covered_artist_count/total_artist_count if total_artist_count else 0:.1f}%)")
    
    # Key recommendations
    print(f"\n10. KEY FINDINGS:")
    
    # Find most important missing genres
    important_missing = []
    for genre, count in new_genres_with_count[:30]:
        if count >= 3:  # Appears in at least 3 artists
            important_missing.append((genre, count))
    
    if important_missing[:10]:
        print("\n   CRITICAL GAPS - High-frequency genres to add:")
        for genre, count in important_missing[:10]:
            print(f"   - {genre:40} ({count} artists)")
            
            # Suggest how to integrate
            suggestions = []
            if 'rock' in genre:
                suggestions.append("rock family")
            if 'pop' in genre:
                suggestions.append("pop family")
            if 'punk' in genre or 'core' in genre:
                suggestions.append("punk/hardcore family")
            if 'soul' in genre or 'funk' in genre:
                suggestions.append("soul/funk family")
            if 'country' in genre or 'americana' in genre:
                suggestions.append("country/folk family")
            if 'wave' in genre:
                suggestions.append("new wave/synth family")
                
            if suggestions:
                print(f"     → Integrate into: {', '.join(suggestions)}")

if __name__ == "__main__":
    analyze_cached_genres()
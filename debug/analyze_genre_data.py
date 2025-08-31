#!/usr/bin/env python3
"""
Analyze the scope of genre data to determine visualization feasibility.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'lib'))

from genre_mapper import GenreMapper
from collections import Counter

def analyze_genre_scope():
    """Analyze how many genres we have and their relationships."""
    mapper = GenreMapper(verbose=False)
    
    print("GENRE DATA ANALYSIS")
    print("=" * 60)
    
    # 1. Count genres in our manual hierarchy
    all_manual_genres = set()
    for genre, relations in mapper.genre_relationships.items():
        all_manual_genres.add(genre)
        all_manual_genres.update(relations.get('subgenres', []))
        all_manual_genres.update(relations.get('siblings', []))
        all_manual_genres.update(relations.get('near_neighbors', []))
        if relations.get('parent'):
            all_manual_genres.add(relations['parent'])
    
    print(f"\n1. MANUAL HIERARCHY:")
    print(f"   Total genres defined: {len(all_manual_genres)}")
    print(f"   Root genres: {len([g for g in mapper.genre_relationships if mapper.genre_relationships[g].get('parent') is None])}")
    
    # 2. Count genres from Spotify cache
    spotify_genres = set()
    for artist_genres in mapper.artist_genres_cache.values():
        spotify_genres.update(artist_genres)
    
    print(f"\n2. SPOTIFY GENRES:")
    print(f"   Unique genres from {len(mapper.artist_genres_cache)} artists: {len(spotify_genres)}")
    
    # 3. Analyze co-occurrence matrix
    print(f"\n3. CO-OCCURRENCE MATRIX:")
    print(f"   Genres with co-occurrence data: {len(mapper.cooccurrence_matrix)}")
    
    # 4. Sample some genre connections
    print(f"\n4. SAMPLE CONNECTIONS (for 'rock'):")
    if 'rock' in mapper.genre_relationships:
        rock_rel = mapper.genre_relationships['rock']
        print(f"   Direct subgenres: {len(rock_rel.get('subgenres', []))}")
        print(f"   Siblings: {len(rock_rel.get('siblings', []))}")
        print(f"   Near neighbors: {len(rock_rel.get('near_neighbors', []))}")
        
        # Count all genres within distance 0.5 of rock
        related = mapper.get_related_genres('rock', max_distance=0.5)
        print(f"   Total genres within distance 0.5: {len(related)}")
    
    # 5. Get genre frequency from artist data
    genre_frequency = Counter()
    for artist_genres in mapper.artist_genres_cache.values():
        for genre in artist_genres:
            genre_frequency[genre] += 1
    
    print(f"\n5. MOST COMMON SPOTIFY GENRES:")
    for genre, count in genre_frequency.most_common(15):
        print(f"   {genre:30} ({count} artists)")
    
    # 6. Estimate visualization complexity
    print(f"\n6. VISUALIZATION COMPLEXITY ESTIMATE:")
    
    # For a focused view (manual hierarchy only)
    print(f"\n   Option A: Manual Hierarchy Only")
    print(f"   - Nodes: {len(all_manual_genres)}")
    print(f"   - Edges: ~{len(all_manual_genres) * 3} (estimated)")
    print(f"   - Feasibility: ✅ GOOD - Small enough for clear visualization")
    
    # For Spotify genres
    print(f"\n   Option B: All Spotify Genres")
    print(f"   - Nodes: {len(spotify_genres)}")
    print(f"   - Edges: ~{len(spotify_genres) * 10} (estimated)")
    print(f"   - Feasibility: ⚠️  CHALLENGING - Would need filtering/clustering")
    
    # For top genres only
    top_20_genres = set(g for g, _ in genre_frequency.most_common(20))
    print(f"\n   Option C: Top 20 Most Common Genres")
    print(f"   - Nodes: 20")
    print(f"   - Edges: ~60-100")
    print(f"   - Feasibility: ✅ EXCELLENT - Perfect for visualization")
    
    # Calculate actual connections for top genres
    print(f"\n7. ACTUAL CONNECTIONS FOR TOP GENRES:")
    connection_counts = []
    for genre in list(top_20_genres)[:10]:
        related = mapper.get_related_genres(genre, max_distance=0.5)
        connection_counts.append((genre, len(related)))
    
    for genre, count in sorted(connection_counts, key=lambda x: x[1], reverse=True):
        print(f"   {genre:30} has {count:3} related genres (≤0.5 distance)")
    
    return {
        'manual_genres': len(all_manual_genres),
        'spotify_genres': len(spotify_genres),
        'top_genres': top_20_genres
    }

if __name__ == "__main__":
    results = analyze_genre_scope()
#!/usr/bin/env ./venv/bin/python3
"""
Analyze voter-song interaction patterns to understand data for preference modeling
"""

import sqlite3
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from setup_db import get_db_connection

def analyze_voting_patterns():
    """Analyze the voting data to understand patterns for preference modeling"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🔍 VOTER PREFERENCE MODELING - DATA ANALYSIS")
    print("=" * 60)
    print()
    
    # 1. Basic voting statistics
    print("📊 BASIC VOTING STATISTICS")
    print("-" * 30)
    
    cursor.execute("SELECT COUNT(DISTINCT voter) as unique_voters FROM votes")
    unique_voters = cursor.fetchone()['unique_voters']
    print(f"Unique voters: {unique_voters}")
    
    cursor.execute("SELECT COUNT(*) as total_votes FROM votes")
    total_votes = cursor.fetchone()['total_votes']
    print(f"Total votes cast: {total_votes}")
    
    cursor.execute("SELECT AVG(points) as avg_points FROM votes WHERE points IS NOT NULL")
    avg_points = cursor.fetchone()['avg_points']
    print(f"Average points per vote: {avg_points:.2f}")
    
    cursor.execute("SELECT COUNT(DISTINCT song_id) as unique_songs FROM votes")
    unique_songs = cursor.fetchone()['unique_songs']
    print(f"Unique songs voted on: {unique_songs}")
    
    print()
    
    # 2. Voter activity levels
    print("👥 VOTER ACTIVITY ANALYSIS")
    print("-" * 30)
    
    cursor.execute("""
        SELECT voter, COUNT(*) as vote_count, AVG(points) as avg_score
        FROM votes 
        WHERE points IS NOT NULL
        GROUP BY voter 
        ORDER BY vote_count DESC
    """)
    
    voter_stats = cursor.fetchall()
    
    print(f"Most active voters:")
    for i, voter in enumerate(voter_stats[:5]):
        print(f"  {i+1}. {voter['voter']}: {voter['vote_count']} votes, avg {voter['avg_score']:.2f} points")
    
    vote_counts = [v['vote_count'] for v in voter_stats]
    print(f"\nVoting frequency distribution:")
    print(f"  Median votes per voter: {np.median(vote_counts):.0f}")
    print(f"  Min votes: {min(vote_counts)}, Max votes: {max(vote_counts)}")
    
    # Active voters (voted >10 times)
    active_voters = [v for v in voter_stats if v['vote_count'] >= 10]
    print(f"  Active voters (10+ votes): {len(active_voters)}/{len(voter_stats)}")
    
    print()
    
    # 3. Voting behavior patterns
    print("🎯 VOTING BEHAVIOR PATTERNS")
    print("-" * 30)
    
    cursor.execute("""
        SELECT points, COUNT(*) as count
        FROM votes 
        WHERE points IS NOT NULL
        GROUP BY points 
        ORDER BY points
    """)
    
    point_distribution = cursor.fetchall()
    print("Point distribution:")
    for point in point_distribution:
        percentage = (point['count'] / total_votes) * 100
        print(f"  {point['points']} points: {point['count']} votes ({percentage:.1f}%)")
    
    print()
    
    # 4. Voter-song matrix density
    print("📈 VOTER-SONG INTERACTION MATRIX")
    print("-" * 30)
    
    # Calculate matrix sparsity
    possible_interactions = unique_voters * unique_songs
    actual_interactions = total_votes
    density = (actual_interactions / possible_interactions) * 100
    
    print(f"Matrix dimensions: {unique_voters} voters × {unique_songs} songs")
    print(f"Possible interactions: {possible_interactions:,}")
    print(f"Actual interactions: {actual_interactions:,}")
    print(f"Matrix density: {density:.2f}%")
    print(f"Sparsity: {100-density:.2f}%")
    
    print()
    
    # 5. Genre/artist preferences (if we can infer)
    print("🎵 PREFERENCE PATTERNS")
    print("-" * 30)
    
    # Most loved songs (high average scores)
    cursor.execute("""
        SELECT s.title, s.artist, COUNT(v.points) as vote_count, AVG(v.points) as avg_score
        FROM songs s
        JOIN votes v ON s.id = v.song_id
        WHERE v.points IS NOT NULL AND v.points > 0
        GROUP BY s.id
        HAVING vote_count >= 5
        ORDER BY avg_score DESC, vote_count DESC
        LIMIT 10
    """)
    
    loved_songs = cursor.fetchall()
    print("Most loved songs (avg score, 5+ votes):")
    for i, song in enumerate(loved_songs):
        print(f"  {i+1}. {song['title']} by {song['artist']}: {song['avg_score']:.2f} avg ({song['vote_count']} votes)")
    
    print()
    
    # 6. Voter agreement analysis
    print("🤝 VOTER AGREEMENT ANALYSIS")
    print("-" * 30)
    
    # Find pairs of voters who often vote on the same songs
    cursor.execute("""
        SELECT v1.voter as voter1, v2.voter as voter2, COUNT(*) as shared_votes,
               AVG(ABS(v1.points - v2.points)) as avg_difference
        FROM votes v1
        JOIN votes v2 ON v1.song_id = v2.song_id
        WHERE v1.voter < v2.voter AND v1.points IS NOT NULL AND v2.points IS NOT NULL
        GROUP BY v1.voter, v2.voter
        HAVING shared_votes >= 10
        ORDER BY avg_difference ASC, shared_votes DESC
        LIMIT 5
    """)
    
    similar_voters = cursor.fetchall()
    print("Most similar voter pairs (10+ shared votes):")
    for pair in similar_voters:
        print(f"  {pair['voter1']} & {pair['voter2']}: {pair['shared_votes']} shared votes, "
              f"{pair['avg_difference']:.2f} avg point difference")
    
    print()
    
    # 7. Round-specific patterns
    print("🔄 ROUND-SPECIFIC PATTERNS")
    print("-" * 30)
    
    cursor.execute("""
        SELECT r.title as round_title, COUNT(DISTINCT v.voter) as unique_voters,
               COUNT(v.points) as total_votes, AVG(v.points) as avg_score
        FROM rounds r
        JOIN songs s ON r.id = s.round_id
        JOIN votes v ON s.id = v.song_id
        WHERE v.points IS NOT NULL
        GROUP BY r.id
        ORDER BY unique_voters DESC
        LIMIT 10
    """)
    
    round_stats = cursor.fetchall()
    print("Most participated rounds:")
    for round_data in round_stats:
        print(f"  '{round_data['round_title']}': {round_data['unique_voters']} voters, "
              f"{round_data['total_votes']} votes, {round_data['avg_score']:.2f} avg")
    
    print()
    
    # 8. Recommendations for modeling approach
    print("💡 MODELING RECOMMENDATIONS")
    print("-" * 30)
    
    if density < 1.0:
        print("⚠️  Very sparse matrix - collaborative filtering will be challenging")
        print("   Recommend: Hybrid approach with content-based features")
    elif density < 5.0:
        print("📊 Moderately sparse matrix - good for collaborative filtering with regularization")
    else:
        print("✅ Dense matrix - excellent for collaborative filtering")
    
    if len(active_voters) >= 10:
        print(f"✅ Sufficient active voters ({len(active_voters)}) for meaningful clustering")
    else:
        print("⚠️  Limited active voters - may need simpler preference modeling")
    
    if unique_songs >= 100:
        print(f"✅ Good song variety ({unique_songs}) for preference learning")
    else:
        print("⚠️  Limited song variety - preferences may be too specific")
    
    conn.close()
    
    return {
        'unique_voters': unique_voters,
        'total_votes': total_votes,
        'unique_songs': unique_songs,
        'density': density,
        'active_voters': len(active_voters),
        'avg_points': avg_points
    }

if __name__ == "__main__":
    analyze_voting_patterns()
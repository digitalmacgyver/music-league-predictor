#!/usr/bin/env ./venv/bin/python3
"""
Debug voter similarity calculations to understand potential issues
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from setup_db import get_db_connection

def debug_voter_analysis():
    """Debug the voter analysis to understand discrepancies"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("="*70)
    print("DEBUGGING VOTER ANALYSIS")
    print("="*70)
    
    # First, let's get BT26 voters
    cursor.execute("""
        SELECT DISTINCT v.voter
        FROM votes v
        JOIN songs s ON v.song_id = s.id
        JOIN rounds r ON s.round_id = r.id
        JOIN leagues l ON r.league_id = l.id
        WHERE l.title LIKE '%Bard%Tale%26%'
        ORDER BY v.voter
    """)
    
    bt26_voters = [row['voter'] for row in cursor.fetchall()]
    print(f"\nBT26 Voters ({len(bt26_voters)}):")
    for v in bt26_voters:
        print(f"  • {v}")
    
    # Now let's check TOTAL votes for each voter (including 0-point votes)
    print("\n" + "-"*70)
    print("TOTAL VOTE COUNTS (All votes, including 0 points)")
    print("-"*70)
    
    for voter in ['Joe Hayward', 'legion1996a', 'Adam Gimpert', 'Drew']:
        # Count ALL votes
        cursor.execute("""
            SELECT COUNT(*) as total_votes,
                   SUM(CASE WHEN points > 0 THEN 1 ELSE 0 END) as positive_votes,
                   SUM(CASE WHEN points = 0 THEN 1 ELSE 0 END) as zero_votes,
                   COUNT(DISTINCT s.round_id) as rounds_participated,
                   COUNT(DISTINCT r.league_id) as leagues_participated
            FROM votes v
            JOIN songs s ON v.song_id = s.id
            JOIN rounds r ON s.round_id = r.id
            WHERE v.voter = ?
        """, (voter,))
        
        result = cursor.fetchone()
        print(f"\n{voter}:")
        print(f"  Total votes: {result['total_votes']}")
        print(f"  Positive votes (1-5 points): {result['positive_votes']}")
        print(f"  Zero votes: {result['zero_votes']}")
        print(f"  Rounds participated: {result['rounds_participated']}")
        print(f"  Leagues participated: {result['leagues_participated']}")
    
    # Check overlap between specific voter pairs
    print("\n" + "-"*70)
    print("VOTER OVERLAP ANALYSIS")
    print("-"*70)
    
    test_pairs = [
        ('Adam Gimpert', 'Joe Hayward'),
        ('Adam Gimpert', 'Matt M'),
        ('Drew', 'Joe Hayward'),
        ('legion1996a', 'Joe Hayward')
    ]
    
    for voter1, voter2 in test_pairs:
        # Count songs both voters rated
        cursor.execute("""
            SELECT COUNT(DISTINCT v1.song_id) as shared_songs,
                   COUNT(DISTINCT CASE WHEN v1.points > 0 AND v2.points > 0 THEN v1.song_id END) as both_positive,
                   AVG(ABS(v1.points - v2.points)) as avg_difference
            FROM votes v1
            JOIN votes v2 ON v1.song_id = v2.song_id
            WHERE v1.voter = ? AND v2.voter = ?
        """, (voter1, voter2))
        
        result = cursor.fetchone()
        print(f"\n{voter1} vs {voter2}:")
        print(f"  Songs both voted on: {result['shared_songs']}")
        print(f"  Songs both gave positive points: {result['both_positive']}")
        if result['avg_difference'] is not None:
            print(f"  Avg point difference: {result['avg_difference']:.2f}")
    
    # Now let's recalculate similarity using ONLY shared songs
    print("\n" + "-"*70)
    print("RECALCULATED SIMILARITY (Only shared songs with positive votes)")
    print("-"*70)
    
    for voter1, voter2 in test_pairs:
        # Get only songs both voters gave positive points to
        cursor.execute("""
            SELECT v1.song_id, v1.points as points1, v2.points as points2
            FROM votes v1
            JOIN votes v2 ON v1.song_id = v2.song_id
            WHERE v1.voter = ? AND v2.voter = ?
              AND v1.points > 0 AND v2.points > 0
        """, (voter1, voter2))
        
        shared_votes = cursor.fetchall()
        
        if len(shared_votes) >= 10:  # Need minimum overlap
            vec1 = np.array([v['points1'] for v in shared_votes])
            vec2 = np.array([v['points2'] for v in shared_votes])
            
            # Calculate cosine similarity
            cos_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            print(f"\n{voter1} vs {voter2}:")
            print(f"  Shared positive votes: {len(shared_votes)}")
            print(f"  Cosine similarity: {cos_sim:.3f}")
        else:
            print(f"\n{voter1} vs {voter2}:")
            print(f"  Insufficient overlap ({len(shared_votes)} shared positive votes)")
    
    # Check for rule violations affecting counts
    print("\n" + "-"*70)
    print("RULE VIOLATIONS CHECK")
    print("-"*70)
    
    cursor.execute("""
        SELECT COUNT(*) as violation_count
        FROM songs s
        WHERE s.num_voters != s.num_voters_awarded
    """)
    
    violations = cursor.fetchone()
    print(f"Songs with rule violations: {violations['violation_count']}")
    
    # Check specific leagues Adam participated in
    print("\n" + "-"*70)
    print("ADAM GIMPERT'S PARTICIPATION")
    print("-"*70)
    
    cursor.execute("""
        SELECT DISTINCT l.title, COUNT(DISTINCT r.id) as rounds_voted
        FROM votes v
        JOIN songs s ON v.song_id = s.id
        JOIN rounds r ON s.round_id = r.id
        JOIN leagues l ON r.league_id = l.id
        WHERE v.voter = 'Adam Gimpert'
        GROUP BY l.id
        ORDER BY l.title
    """)
    
    leagues = cursor.fetchall()
    print(f"Adam Gimpert participated in {len(leagues)} leagues:")
    for league in leagues:
        print(f"  • {league['title']}: {league['rounds_voted']} rounds")
    
    conn.close()

if __name__ == "__main__":
    debug_voter_analysis()
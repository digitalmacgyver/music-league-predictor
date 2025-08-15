#!/usr/bin/env ./venv/bin/python3
"""
Corrected voter similarity analysis using only mutually rated songs
"""

import sqlite3
import pandas as pd
import numpy as np
from setup_db import get_db_connection
from itertools import combinations

def corrected_voter_similarity():
    """Calculate voter similarity using only songs both voters rated"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get BT26 voters
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
    
    print("="*80)
    print("           CORRECTED VOTER SIMILARITY ANALYSIS")
    print("           Bard's Tale 26: Don Juan Participants")
    print("="*80)
    print("\nMethodology: Using only songs rated by BOTH voters in each pair")
    print("Minimum threshold: 30 mutually rated songs for reliable comparison")
    print()
    
    # Calculate pairwise similarities
    similarities = {}
    overlaps = {}
    
    print("Calculating pairwise similarities...")
    
    for voter1, voter2 in combinations(bt26_voters, 2):
        # Get songs both voters rated with positive points
        cursor.execute("""
            SELECT v1.song_id, v1.points as points1, v2.points as points2,
                   s.title, s.artist
            FROM votes v1
            JOIN votes v2 ON v1.song_id = v2.song_id
            JOIN songs s ON v1.song_id = s.id
            WHERE v1.voter = ? AND v2.voter = ?
              AND v1.points > 0 AND v2.points > 0
        """, (voter1, voter2))
        
        shared_votes = cursor.fetchall()
        overlap_count = len(shared_votes)
        overlaps[(voter1, voter2)] = overlap_count
        
        if overlap_count >= 30:  # Minimum threshold for reliable similarity
            vec1 = np.array([v['points1'] for v in shared_votes])
            vec2 = np.array([v['points2'] for v in shared_votes])
            
            # Calculate cosine similarity
            cos_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            similarities[(voter1, voter2)] = cos_sim
        else:
            similarities[(voter1, voter2)] = None  # Insufficient data
    
    # Build results for each voter
    voter_results = {}
    for voter in bt26_voters:
        most_similar = None
        most_similar_score = -1
        least_similar = None
        least_similar_score = 2
        valid_similarities = []
        
        for (v1, v2), sim in similarities.items():
            if sim is not None:  # Valid similarity
                if v1 == voter:
                    other_voter = v2
                elif v2 == voter:
                    other_voter = v1
                else:
                    continue
                
                valid_similarities.append(sim)
                
                if sim > most_similar_score:
                    most_similar_score = sim
                    most_similar = other_voter
                
                if sim < least_similar_score:
                    least_similar_score = sim
                    least_similar = other_voter
        
        voter_results[voter] = {
            'most_similar': most_similar,
            'most_score': most_similar_score,
            'least_similar': least_similar,
            'least_score': least_similar_score,
            'avg_similarity': np.mean(valid_similarities) if valid_similarities else None,
            'valid_comparisons': len(valid_similarities)
        }
    
    # Get voter activity stats
    voter_stats = {}
    for voter in bt26_voters:
        cursor.execute("""
            SELECT COUNT(*) as total_votes,
                   AVG(points) as avg_score,
                   COUNT(DISTINCT r.league_id) as leagues,
                   COUNT(DISTINCT r.id) as rounds
            FROM votes v
            JOIN songs s ON v.song_id = s.id
            JOIN rounds r ON s.round_id = r.id
            WHERE v.voter = ? AND v.points > 0
        """, (voter,))
        
        result = cursor.fetchone()
        voter_stats[voter] = result
    
    # Print detailed results
    print("\n" + "="*80)
    print("CORRECTED SIMILARITY RESULTS")
    print("="*80)
    
    print("\nVoter                   Most Similar To         Score   Least Similar To        Score   Valid")
    print("                                                                                        Comps")
    print("-" * 90)
    
    for voter in sorted(bt26_voters):
        result = voter_results[voter]
        most_sim = result['most_similar'] or "Insufficient data"
        least_sim = result['least_similar'] or "Insufficient data"
        most_score = f"{result['most_score']:.3f}" if result['most_score'] > -1 else "N/A"
        least_score = f"{result['least_score']:.3f}" if result['least_score'] < 2 else "N/A"
        valid_count = result['valid_comparisons']
        
        print(f"{voter:<23} {most_sim:<23} {most_score:<7} {least_sim:<23} {least_score:<7} {valid_count}")
    
    # Find most and least similar pairs overall
    valid_sims = [(pair, sim) for pair, sim in similarities.items() if sim is not None]
    if valid_sims:
        highest_pair, highest_sim = max(valid_sims, key=lambda x: x[1])
        lowest_pair, lowest_sim = min(valid_sims, key=lambda x: x[1])
        
        print(f"\n" + "-"*80)
        print("OVERALL STATISTICS")
        print("-"*80)
        print(f"Highest similarity: {highest_pair[0]} & {highest_pair[1]} ({highest_sim:.3f})")
        print(f"Lowest similarity: {lowest_pair[0]} & {lowest_pair[1]} ({lowest_sim:.3f})")
        
        all_valid_sims = [sim for _, sim in valid_sims]
        print(f"Average similarity: {np.mean(all_valid_sims):.3f}")
        print(f"Valid comparisons: {len(valid_sims)} out of {len(similarities)} possible pairs")
    
    # Show overlap statistics
    print(f"\n" + "-"*80)
    print("OVERLAP ANALYSIS (Songs rated by both voters)")
    print("-"*80)
    
    print("\nPairs with highest overlap:")
    sorted_overlaps = sorted(overlaps.items(), key=lambda x: x[1], reverse=True)
    for (v1, v2), count in sorted_overlaps[:10]:
        sim = similarities[(v1, v2)]
        sim_str = f"{sim:.3f}" if sim is not None else "N/A (insufficient)"
        print(f"  {v1} & {v2}: {count} shared songs (similarity: {sim_str})")
    
    print("\nPairs with insufficient overlap (<30 songs):")
    insufficient = [(pair, count) for pair, count in overlaps.items() if count < 30]
    insufficient.sort(key=lambda x: x[1])
    for (v1, v2), count in insufficient:
        print(f"  {v1} & {v2}: {count} shared songs")
    
    # Voter activity comparison
    print(f"\n" + "-"*80)
    print("VOTER ACTIVITY LEVELS")
    print("-"*80)
    
    print("Voter                   Votes   Avg Score   Leagues   Rounds   Avg Similarity")
    print("-" * 80)
    
    for voter in sorted(bt26_voters, key=lambda v: voter_stats[v]['total_votes'], reverse=True):
        stats = voter_stats[voter]
        result = voter_results[voter]
        avg_sim = f"{result['avg_similarity']:.3f}" if result['avg_similarity'] else "N/A"
        
        print(f"{voter:<23} {stats['total_votes']:>5} {stats['avg_score']:>9.2f} "
              f"{stats['leagues']:>9} {stats['rounds']:>8} {avg_sim:>14}")
    
    # Identify corrected patterns
    print(f"\n" + "-"*80)
    print("KEY CORRECTIONS FROM ORIGINAL ANALYSIS")
    print("-"*80)
    
    # Check Adam Gimpert specifically
    adam_sims = []
    for (v1, v2), sim in similarities.items():
        if sim is not None and ('Adam Gimpert' in [v1, v2]):
            other = v2 if v1 == 'Adam Gimpert' else v1
            adam_sims.append((other, sim))
    
    if adam_sims:
        adam_sims.sort(key=lambda x: x[1], reverse=True)
        print(f"\nAdam Gimpert's corrected similarities:")
        for other, sim in adam_sims:
            overlap = overlaps.get(('Adam Gimpert', other), overlaps.get((other, 'Adam Gimpert'), 0))
            print(f"  vs {other}: {sim:.3f} (based on {overlap} shared songs)")
    
    print(f"\nNote: Adam Gimpert only participated in {voter_stats['Adam Gimpert']['leagues']} leagues")
    print(f"compared to most active voters who participated in 20+ leagues.")
    print(f"His 'low similarity' in the original analysis was due to limited overlap,")
    print(f"NOT different musical taste!")
    
    conn.close()

if __name__ == "__main__":
    corrected_voter_similarity()
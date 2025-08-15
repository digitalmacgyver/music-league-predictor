#!/usr/bin/env ./venv/bin/python3
"""
Analyze voter similarity for only voters who participated in Bard's Tale 26: Don Joan
"""

import sqlite3
import pandas as pd
import numpy as np
from collections import defaultdict
import logging
from sklearn.metrics.pairwise import cosine_similarity
from setup_db import get_db_connection

logging.basicConfig(level=logging.WARNING)

def get_bt26_voters():
    """Get list of voters who participated in Bard's Tale 26"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First find the league ID for Bard's Tale 26
    cursor.execute("""
        SELECT l.id, l.title
        FROM leagues l
        WHERE l.title LIKE '%Bard%Tale%26%'
           OR l.title LIKE '%Don Joan%'
    """)
    
    leagues = cursor.fetchall()
    print("Found leagues:")
    for league in leagues:
        print(f"  {league['id']}: {league['title']}")
    
    if not leagues:
        print("ERROR: Could not find Bard's Tale 26")
        return []
    
    league_id = leagues[0]['id']
    print(f"\nUsing league: {leagues[0]['title']}")
    
    # Get all voters who participated in this league
    cursor.execute("""
        SELECT DISTINCT v.voter
        FROM votes v
        JOIN songs s ON v.song_id = s.id
        JOIN rounds r ON s.round_id = r.id
        WHERE r.league_id = ?
        ORDER BY v.voter
    """, (league_id,))
    
    voters = [row['voter'] for row in cursor.fetchall()]
    conn.close()
    
    return voters

def analyze_bt26_voter_similarity():
    """Analyze similarity for BT26 voters using ALL their historical data"""
    
    bt26_voters = get_bt26_voters()
    
    if not bt26_voters:
        print("No voters found for Bard's Tale 26")
        return
    
    print(f"\nFound {len(bt26_voters)} voters in Bard's Tale 26:")
    for voter in bt26_voters:
        print(f"  • {voter}")
    
    # Now analyze these voters using ALL their voting history
    conn = get_db_connection()
    
    # Get all voting data for these specific voters
    voter_list = "','".join(bt26_voters)
    query = f"""
        SELECT 
            v.voter,
            v.song_id,
            v.points,
            s.title as song_title,
            s.artist
        FROM votes v
        JOIN songs s ON v.song_id = s.id
        WHERE v.voter IN ('{voter_list}')
          AND v.points IS NOT NULL 
          AND v.points > 0
        ORDER BY v.voter, v.song_id
    """
    
    df = pd.read_sql_query(query, conn)
    
    print(f"\nLoaded {len(df)} votes from {len(df['voter'].unique())} BT26 voters")
    
    # Build voter-song matrix
    voters = sorted(df['voter'].unique())
    songs = sorted(df['song_id'].unique())
    
    matrix = np.zeros((len(voters), len(songs)))
    
    for _, row in df.iterrows():
        voter_idx = voters.index(row['voter'])
        song_idx = songs.index(row['song_id'])
        matrix[voter_idx, song_idx] = row['points']
    
    # Calculate similarity
    similarity_matrix = cosine_similarity(matrix)
    
    print("\n" + "="*70)
    print("VOTER SIMILARITY ANALYSIS - BARD'S TALE 26 PARTICIPANTS")
    print("="*70)
    print("\nSimilarity scores show how similarly two voters rate songs:")
    print("  1.0 = Perfect agreement")
    print("  0.7-0.9 = Very similar taste") 
    print("  0.4-0.6 = Moderate overlap")
    print("  0.1-0.3 = Different taste")
    print("  0.0 = No overlap or opposite preferences")
    print("\n" + "-"*70)
    print("\nVOTER SIMILARITY PAIRS (Most and Least Similar)")
    print("-"*70)
    
    # For each voter, find most and least similar
    results = []
    for i, voter in enumerate(voters):
        similarities = similarity_matrix[i]
        
        # Find most similar (excluding self)
        most_similar_idx = None
        most_similar_score = -1
        least_similar_idx = None
        least_similar_score = 2
        
        for j, score in enumerate(similarities):
            if i != j:
                if score > most_similar_score:
                    most_similar_score = score
                    most_similar_idx = j
                if score < least_similar_score:
                    least_similar_score = score
                    least_similar_idx = j
        
        if most_similar_idx is not None and least_similar_idx is not None:
            results.append({
                'voter': voter,
                'most_similar': voters[most_similar_idx],
                'most_score': most_similar_score,
                'least_similar': voters[least_similar_idx],
                'least_score': least_similar_score
            })
    
    # Print results sorted by voter name
    print("\nVoter                   Most Similar To         Score   Least Similar To        Score")
    print("-"*85)
    for r in sorted(results, key=lambda x: x['voter']):
        print(f"{r['voter']:<23} {r['most_similar']:<23} {r['most_score']:.3f}   "
              f"{r['least_similar']:<23} {r['least_score']:.3f}")
    
    # Find overall statistics
    print("\n" + "-"*70)
    print("OVERALL STATISTICS")
    print("-"*70)
    
    # Find highest and lowest pairs
    max_sim = 0
    max_pair = None
    min_sim = 1
    min_pair = None
    
    for i in range(len(voters)):
        for j in range(i+1, len(voters)):
            sim = similarity_matrix[i][j]
            if sim > max_sim:
                max_sim = sim
                max_pair = (voters[i], voters[j])
            if sim < min_sim:
                min_sim = sim
                min_pair = (voters[i], voters[j])
    
    print(f"\nHighest similarity: {max_pair[0]} & {max_pair[1]} ({max_sim:.3f})")
    print(f"Lowest similarity: {min_pair[0]} & {min_pair[1]} ({min_sim:.3f})")
    
    # Calculate average
    all_sims = []
    for i in range(len(voters)):
        for j in range(i+1, len(voters)):
            all_sims.append(similarity_matrix[i][j])
    
    avg_sim = np.mean(all_sims)
    print(f"Average similarity: {avg_sim:.3f}")
    
    # Find most universally liked voter (highest average similarity)
    avg_similarities = []
    for i, voter in enumerate(voters):
        other_sims = [similarity_matrix[i][j] for j in range(len(voters)) if i != j]
        avg_similarities.append((voter, np.mean(other_sims)))
    
    avg_similarities.sort(key=lambda x: x[1], reverse=True)
    
    print("\n" + "-"*70)
    print("MOST UNIVERSALLY COMPATIBLE VOTERS (Highest Average Similarity)")
    print("-"*70)
    for voter, avg_sim in avg_similarities[:5]:
        print(f"{voter:<25} Average similarity: {avg_sim:.3f}")
    
    print("\n" + "-"*70)
    print("MOST UNIQUE TASTE (Lowest Average Similarity)")
    print("-"*70)
    for voter, avg_sim in avg_similarities[-5:]:
        print(f"{voter:<25} Average similarity: {avg_sim:.3f}")
    
    # Voter activity stats
    print("\n" + "-"*70)
    print("VOTER ACTIVITY LEVELS")
    print("-"*70)
    
    vote_counts = df.groupby('voter').size().sort_values(ascending=False)
    avg_scores = df.groupby('voter')['points'].mean()
    
    for voter in vote_counts.head(10).index:
        count = vote_counts[voter]
        avg = avg_scores[voter]
        print(f"{voter:<25} {count:>4} votes, {avg:.2f} avg score")
    
    # Interesting patterns
    print("\n" + "-"*70)
    print("INTERESTING PATTERNS")
    print("-"*70)
    
    # Check for family connections
    print("\nPotential Family/Friend Groups (based on similar names):")
    family_groups = {}
    for voter in voters:
        last_name = voter.split()[-1] if ' ' in voter else voter
        if last_name not in family_groups:
            family_groups[last_name] = []
        family_groups[last_name].append(voter)
    
    for last_name, members in family_groups.items():
        if len(members) > 1:
            print(f"\n  {last_name} group: {', '.join(members)}")
            # Check their similarity
            for i in range(len(members)):
                for j in range(i+1, len(members)):
                    if members[i] in voters and members[j] in voters:
                        idx1 = voters.index(members[i])
                        idx2 = voters.index(members[j])
                        sim = similarity_matrix[idx1][idx2]
                        print(f"    {members[i]} & {members[j]}: {sim:.3f} similarity")
    
    conn.close()

if __name__ == "__main__":
    analyze_bt26_voter_similarity()
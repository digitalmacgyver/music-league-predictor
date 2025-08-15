#!/usr/bin/env ./venv/bin/python3
"""
Analyze BT26 voters using only data from the most recent 4 leagues 
where most/all participants were active
"""

import sqlite3
import pandas as pd
import numpy as np
from setup_db import get_db_connection
from itertools import combinations

def analyze_recent_leagues():
    """Find and analyze the most recent leagues with high BT26 participation"""
    
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
    bt26_set = set(bt26_voters)
    
    print("Finding recent leagues with high BT26 participation...")
    
    # Find leagues ordered by recency with BT26 participation counts
    cursor.execute("""
        SELECT l.id, l.title, l.created_at,
               COUNT(DISTINCT v.voter) as total_voters,
               COUNT(DISTINCT CASE WHEN v.voter IN ({}) THEN v.voter END) as bt26_voters,
               COUNT(DISTINCT r.id) as rounds
        FROM leagues l
        JOIN rounds r ON l.id = r.league_id
        JOIN songs s ON r.id = s.round_id
        JOIN votes v ON s.id = v.song_id
        WHERE v.points > 0
        GROUP BY l.id
        HAVING bt26_voters >= 8  -- At least 8 BT26 voters participated
        ORDER BY l.created_at DESC
        LIMIT 10
    """.format(','.join([f"'{v}'" for v in bt26_voters])))
    
    recent_leagues = cursor.fetchall()
    
    print("\nRecent leagues with high BT26 participation:")
    for i, league in enumerate(recent_leagues):
        print(f"{i+1:2}. {league['title']} - {league['bt26_voters']}/{len(bt26_voters)} BT26 voters ({league['rounds']} rounds)")
    
    # Take the 4 most recent leagues with good participation
    selected_leagues = recent_leagues[:4]
    league_ids = [l['id'] for l in selected_leagues]
    
    print(f"\nAnalyzing these 4 recent leagues:")
    for league in selected_leagues:
        print(f"  • {league['title']} ({league['bt26_voters']}/{len(bt26_voters)} BT26 voters)")
    
    # Get voting data from these leagues only
    league_id_str = ','.join([f"'{lid}'" for lid in league_ids])
    
    query = f"""
        SELECT v.voter, v.song_id, v.points, s.title, s.artist,
               r.title as round_title, l.title as league_title
        FROM votes v
        JOIN songs s ON v.song_id = s.id
        JOIN rounds r ON s.round_id = r.id
        JOIN leagues l ON r.league_id = l.id
        WHERE l.id IN ({league_id_str})
          AND v.voter IN ({','.join([f"'{v}'" for v in bt26_voters])})
          AND v.points > 0
        ORDER BY l.created_at DESC, r.round_number, v.voter
    """
    
    df = pd.read_sql_query(query, conn)
    
    print(f"\nLoaded {len(df)} votes from {len(df['voter'].unique())} BT26 voters in recent leagues")
    
    # Analyze participation in these specific leagues
    participation = df.groupby(['voter', 'league_title']).size().unstack(fill_value=0)
    
    print("\nParticipation matrix (votes per league):")
    print(participation.to_string())
    
    # Calculate similarities using only this recent data
    recent_voters = list(df['voter'].unique())
    similarities = {}
    overlaps = {}
    
    for voter1, voter2 in combinations(recent_voters, 2):
        # Get shared songs from recent leagues
        v1_data = df[df['voter'] == voter1]
        v2_data = df[df['voter'] == voter2]
        
        # Find songs both rated
        shared_songs = set(v1_data['song_id']).intersection(set(v2_data['song_id']))
        
        if len(shared_songs) >= 20:  # Lower threshold for recent data
            v1_scores = []
            v2_scores = []
            
            for song_id in shared_songs:
                v1_score = v1_data[v1_data['song_id'] == song_id]['points'].iloc[0]
                v2_score = v2_data[v2_data['song_id'] == song_id]['points'].iloc[0]
                v1_scores.append(v1_score)
                v2_scores.append(v2_score)
            
            # Calculate cosine similarity
            vec1 = np.array(v1_scores)
            vec2 = np.array(v2_scores)
            cos_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            similarities[(voter1, voter2)] = cos_sim
            overlaps[(voter1, voter2)] = len(shared_songs)
        else:
            similarities[(voter1, voter2)] = None
            overlaps[(voter1, voter2)] = len(shared_songs)
    
    # Calculate voter statistics for recent leagues
    voter_stats = {}
    for voter in recent_voters:
        voter_data = df[df['voter'] == voter]
        leagues_participated = voter_data['league_title'].nunique()
        total_votes = len(voter_data)
        avg_score = voter_data['points'].mean()
        score_variance = voter_data['points'].var()
        
        # Calculate consistency (how often they deviate from their average)
        deviations = abs(voter_data['points'] - avg_score)
        consistency = 1 / (deviations.mean() + 0.1)
        
        voter_stats[voter] = {
            'total_votes': total_votes,
            'leagues_participated': leagues_participated,
            'avg_score': avg_score,
            'score_variance': score_variance,
            'consistency': consistency
        }
    
    return df, similarities, overlaps, voter_stats, selected_leagues, recent_voters

def generate_insights_report(df, similarities, overlaps, voter_stats, leagues, voters):
    """Generate focused insights report"""
    
    print("\n" + "="*80)
    print("    FRESH INSIGHTS: BT26 VOTERS IN RECENT LEAGUES")
    print("="*80)
    
    league_names = [l['title'] for l in leagues]
    print(f"\nAnalyzing: {', '.join(league_names)}")
    print(f"Voters: {len(voters)} BT26 participants")
    print(f"Total votes: {len(df)}")
    
    # Novel insight 1: Scoring generosity evolution
    print(f"\n" + "-"*80)
    print("SCORING PERSONALITY PROFILES (Recent Leagues Only)")
    print("-"*80)
    
    print("\nVoter                   Avg Score   Consistency   Generosity Style")
    print("-" * 70)
    
    for voter in sorted(voters):
        stats = voter_stats[voter]
        avg = stats['avg_score']
        consistency = stats['consistency']
        
        # Determine generosity style
        if avg >= 1.6:
            style = "Liberal scorer"
        elif avg <= 1.2:
            style = "Conservative critic"
        else:
            style = "Balanced rater"
        
        # Add consistency descriptor
        if consistency >= 2.0:
            consistency_desc = "Very consistent"
        elif consistency >= 1.5:
            consistency_desc = "Moderately consistent"
        else:
            consistency_desc = "Variable scoring"
        
        print(f"{voter:<23} {avg:>8.2f} {consistency:>12.2f}   {style} ({consistency_desc})")
    
    # Novel insight 2: Song preference convergence
    print(f"\n" + "-"*80)
    print("MUSICAL CONVERGENCE ANALYSIS")
    print("-"*80)
    
    # Find songs rated by many voters and analyze agreement
    song_ratings = df.groupby(['song_id', 'title', 'artist']).agg({
        'voter': 'count',
        'points': ['mean', 'std']
    }).reset_index()
    
    song_ratings.columns = ['song_id', 'title', 'artist', 'voter_count', 'avg_rating', 'rating_std']
    
    # High consensus songs (many voters, low disagreement)
    consensus_songs = song_ratings[
        (song_ratings['voter_count'] >= 6) & 
        (song_ratings['rating_std'] <= 0.6)
    ].sort_values('avg_rating', ascending=False)
    
    print("\nHighest consensus songs (6+ voters, low disagreement):")
    for _, song in consensus_songs.head(5).iterrows():
        print(f"  {song['title']} by {song['artist']}")
        print(f"    {song['voter_count']} voters, {song['avg_rating']:.2f} avg, {song['rating_std']:.2f} disagreement")
    
    # Polarizing songs (many voters, high disagreement)
    polarizing_songs = song_ratings[
        (song_ratings['voter_count'] >= 6) & 
        (song_ratings['rating_std'] >= 1.2)
    ].sort_values('rating_std', ascending=False)
    
    print("\nMost polarizing songs (6+ voters, high disagreement):")
    for _, song in polarizing_songs.head(5).iterrows():
        print(f"  {song['title']} by {song['artist']}")
        print(f"    {song['voter_count']} voters, {song['avg_rating']:.2f} avg, {song['rating_std']:.2f} disagreement")
    
    # Novel insight 3: Cross-league consistency
    print(f"\n" + "-"*80)
    print("CROSS-LEAGUE CONSISTENCY PATTERNS")
    print("-"*80)
    
    # Check if voters are consistent across different leagues
    league_consistency = {}
    for voter in voters:
        voter_data = df[df['voter'] == voter]
        league_averages = voter_data.groupby('league_title')['points'].mean()
        
        if len(league_averages) >= 2:  # Participated in multiple leagues
            consistency_score = 1 / (league_averages.std() + 0.1)
            league_consistency[voter] = {
                'consistency': consistency_score,
                'leagues': len(league_averages),
                'avg_range': league_averages.max() - league_averages.min()
            }
    
    print("\nVoter consistency across different leagues:")
    print("Voter                   Leagues   Score Range   Consistency")
    print("-" * 60)
    
    for voter, data in sorted(league_consistency.items(), key=lambda x: x[1]['consistency'], reverse=True):
        print(f"{voter:<23} {data['leagues']:>7} {data['avg_range']:>11.2f} {data['consistency']:>11.2f}")
    
    # Novel insight 4: Recent similarity trends
    print(f"\n" + "-"*80)
    print("RECENT MUSICAL ALIGNMENT (High-Overlap Pairs Only)")
    print("-"*80)
    
    valid_similarities = [(pair, sim, overlaps[pair]) for pair, sim in similarities.items() 
                         if sim is not None and overlaps[pair] >= 30]
    
    valid_similarities.sort(key=lambda x: x[1], reverse=True)
    
    print("\nStrongest recent alignments (30+ shared songs):")
    for (v1, v2), sim, overlap in valid_similarities[:8]:
        print(f"  {v1} & {v2}: {sim:.3f} similarity ({overlap} shared songs)")
    
    # Novel insight 5: Discover hidden music clusters
    print(f"\n" + "-"*80)
    print("HIDDEN MUSICAL TRIBES")
    print("-"*80)
    
    # Group voters by similar average scoring patterns
    high_scorers = [v for v in voters if voter_stats[v]['avg_score'] >= 1.5]
    low_scorers = [v for v in voters if voter_stats[v]['avg_score'] <= 1.3]
    
    print(f"\nGenerous scorers (1.5+ avg): {', '.join(high_scorers)}")
    print(f"Conservative scorers (1.3- avg): {', '.join(low_scorers)}")
    
    # Check if these groups have internal similarity
    if len(high_scorers) >= 2:
        high_scorer_sims = []
        for v1, v2 in combinations(high_scorers, 2):
            if (v1, v2) in similarities and similarities[(v1, v2)] is not None:
                high_scorer_sims.append(similarities[(v1, v2)])
            elif (v2, v1) in similarities and similarities[(v2, v1)] is not None:
                high_scorer_sims.append(similarities[(v2, v1)])
        
        if high_scorer_sims:
            print(f"Generous scorers internal similarity: {np.mean(high_scorer_sims):.3f}")
    
    if len(low_scorers) >= 2:
        low_scorer_sims = []
        for v1, v2 in combinations(low_scorers, 2):
            if (v1, v2) in similarities and similarities[(v1, v2)] is not None:
                low_scorer_sims.append(similarities[(v1, v2)])
            elif (v2, v1) in similarities and similarities[(v2, v1)] is not None:
                low_scorer_sims.append(similarities[(v2, v1)])
        
        if low_scorer_sims:
            print(f"Conservative scorers internal similarity: {np.mean(low_scorer_sims):.3f}")

if __name__ == "__main__":
    df, similarities, overlaps, voter_stats, leagues, voters = analyze_recent_leagues()
    generate_insights_report(df, similarities, overlaps, voter_stats, leagues, voters)
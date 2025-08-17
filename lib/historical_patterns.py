#!/usr/bin/env ./venv/bin/python3
"""
Historical Performance Pattern Analysis

Tracks how group musical preferences evolve as voter pools change over time.
Analyzes performance patterns, voter composition changes, and preference evolution.
"""

import sqlite3
import pandas as pd
import numpy as np
from setup_db import get_db_connection
from itertools import combinations
import re
from collections import defaultdict, Counter
# import matplotlib.pyplot as plt
# import seaborn as sns
from datetime import datetime

class HistoricalPatternAnalyzer:
    """Analyzes historical performance patterns as voter pools evolve"""
    
    def __init__(self):
        self.conn = get_db_connection()
        self.leagues_data = None
        self.voter_evolution = None
        self.performance_trends = None
    
    def load_chronological_data(self):
        """Load league data in chronological order"""
        
        # Extract league numbers for proper sorting
        query = """
            SELECT l.id, l.title, 
                   COUNT(DISTINCT v.voter) as voter_count,
                   COUNT(DISTINCT r.id) as round_count,
                   COUNT(DISTINCT s.id) as song_count,
                   COUNT(v.id) as total_votes,
                   AVG(v.points) as avg_score,
                   GROUP_CONCAT(DISTINCT v.voter) as voters
            FROM leagues l
            JOIN rounds r ON l.id = r.league_id
            JOIN songs s ON r.id = s.round_id
            JOIN votes v ON s.id = v.song_id
            WHERE v.points > 0
            GROUP BY l.id, l.title
            ORDER BY l.title
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Extract league numbers for proper chronological sorting
        def extract_league_number(title):
            # Look for patterns like "Bard's Tale 26", "B6:", etc.
            match = re.search(r'(?:Bard\'s Tale |B)(\d+)', title)
            if match:
                return int(match.group(1))
            return 0
        
        df['league_number'] = df['title'].apply(extract_league_number)
        df = df.sort_values('league_number')
        
        # Split voters string into lists
        df['voter_list'] = df['voters'].apply(lambda x: x.split(',') if x else [])
        
        self.leagues_data = df
        return df
    
    def analyze_voter_pool_evolution(self):
        """Track how voter pools change over time"""
        
        if self.leagues_data is None:
            self.load_chronological_data()
        
        evolution = []
        all_voters = set()
        
        for idx, league in self.leagues_data.iterrows():
            league_voters = set(league['voter_list'])
            all_voters.update(league_voters)
            
            if idx == 0:
                new_voters = league_voters
                returning_voters = set()
                departed_voters = set()
            else:
                prev_league_voters = set(self.leagues_data.iloc[idx-1]['voter_list'])
                new_voters = league_voters - prev_league_voters
                returning_voters = league_voters & prev_league_voters
                departed_voters = prev_league_voters - league_voters
            
            evolution.append({
                'league_number': league['league_number'],
                'league_title': league['title'],
                'total_voters': len(league_voters),
                'new_voters': len(new_voters),
                'returning_voters': len(returning_voters),
                'departed_voters': len(departed_voters),
                'voter_turnover_rate': len(new_voters) / len(league_voters) if league_voters else 0,
                'retention_rate': len(returning_voters) / len(prev_league_voters) if idx > 0 and prev_league_voters else 0,
                'new_voter_names': list(new_voters),
                'departed_voter_names': list(departed_voters),
                'avg_score': league['avg_score']
            })
        
        self.voter_evolution = pd.DataFrame(evolution)
        return self.voter_evolution
    
    def analyze_preference_evolution(self):
        """Analyze how musical preferences change with voter pool composition"""
        
        # Get detailed song performance data by league
        query = """
            SELECT l.title as league_title, l.id as league_id,
                   s.title as song_title, s.artist, s.album,
                   s.total_votes_awarded, s.final_score, s.num_voters,
                   AVG(v.points) as avg_rating,
                   COUNT(v.id) as vote_count,
                   r.title as round_title, r.description as round_description,
                   GROUP_CONCAT(DISTINCT v.voter) as voters_who_rated
            FROM leagues l
            JOIN rounds r ON l.id = r.league_id
            JOIN songs s ON r.id = s.round_id
            LEFT JOIN votes v ON s.id = v.song_id AND v.points > 0
            GROUP BY l.id, s.id
            ORDER BY l.title, r.round_number, s.song_order
        """
        
        songs_df = pd.read_sql_query(query, self.conn)
        
        # Extract league numbers and sort chronologically
        def extract_league_number(title):
            match = re.search(r'(?:Bard\'s Tale |B)(\d+)', title)
            return int(match.group(1)) if match else 0
        
        songs_df['league_number'] = songs_df['league_title'].apply(extract_league_number)
        songs_df = songs_df.sort_values(['league_number', 'song_title'])
        
        # Analyze genre/style patterns over time
        preference_trends = []
        
        for league_num in sorted(songs_df['league_number'].unique()):
            league_songs = songs_df[songs_df['league_number'] == league_num]
            
            # Basic stats
            total_songs = len(league_songs)
            avg_rating = league_songs['avg_rating'].mean()
            avg_votes_per_song = league_songs['vote_count'].mean()
            
            # Analyze artist/genre patterns (simplified)
            top_artists = league_songs.nlargest(5, 'avg_rating')['artist'].tolist()
            
            # Calculate score distribution
            score_std = league_songs['avg_rating'].std()
            score_range = league_songs['avg_rating'].max() - league_songs['avg_rating'].min()
            
            preference_trends.append({
                'league_number': league_num,
                'league_title': league_songs.iloc[0]['league_title'],
                'total_songs': total_songs,
                'avg_rating': avg_rating,
                'rating_std': score_std,
                'rating_range': score_range,
                'avg_votes_per_song': avg_votes_per_song,
                'top_artists': top_artists[:3]  # Top 3 for brevity
            })
        
        self.performance_trends = pd.DataFrame(preference_trends)
        return self.performance_trends
    
    def analyze_voter_impact_on_preferences(self):
        """Analyze how specific voters joining/leaving affects group preferences"""
        
        if self.voter_evolution is None:
            self.analyze_voter_pool_evolution()
        
        impact_analysis = []
        
        for idx, evolution in self.voter_evolution.iterrows():
            if idx == 0:
                continue  # Skip first league (no baseline)
            
            prev_avg = self.voter_evolution.iloc[idx-1]['avg_score']
            curr_avg = evolution['avg_score']
            score_change = curr_avg - prev_avg
            
            # Correlate with voter changes
            new_voter_count = evolution['new_voters']
            departed_voter_count = evolution['departed_voters']
            turnover_rate = evolution['voter_turnover_rate']
            
            impact_analysis.append({
                'league_number': evolution['league_number'],
                'league_title': evolution['league_title'],
                'score_change': score_change,
                'new_voters': new_voter_count,
                'departed_voters': departed_voter_count,
                'turnover_rate': turnover_rate,
                'impact_direction': 'positive' if score_change > 0.1 else 'negative' if score_change < -0.1 else 'neutral',
                'high_turnover': turnover_rate > 0.3
            })
        
        return pd.DataFrame(impact_analysis)
    
    def identify_stable_core_vs_transient_voters(self):
        """Identify voters who form stable core vs those who are transient"""
        
        # Count league participation for each voter
        query = """
            SELECT v.voter, 
                   COUNT(DISTINCT l.id) as leagues_participated,
                   MIN(l.title) as first_league,
                   MAX(l.title) as last_league,
                   COUNT(v.id) as total_votes,
                   AVG(v.points) as avg_score
            FROM votes v
            JOIN songs s ON v.song_id = s.id
            JOIN rounds r ON s.round_id = r.id
            JOIN leagues l ON r.league_id = l.id
            WHERE v.points > 0
            GROUP BY v.voter
            ORDER BY leagues_participated DESC, total_votes DESC
        """
        
        voter_stats = pd.read_sql_query(query, self.conn)
        
        # Classify voters
        total_leagues = len(self.leagues_data)
        
        def classify_voter(row):
            participation_rate = row['leagues_participated'] / total_leagues
            if participation_rate >= 0.7:
                return 'core'
            elif participation_rate >= 0.3:
                return 'regular'
            else:
                return 'transient'
        
        voter_stats['voter_type'] = voter_stats.apply(classify_voter, axis=1)
        
        return voter_stats
    
    def analyze_era_transitions(self):
        """Identify major transition points in group preferences"""
        
        if self.performance_trends is None:
            self.analyze_preference_evolution()
        
        transitions = []
        
        # Look for significant changes in average rating patterns
        for idx in range(1, len(self.performance_trends)):
            curr = self.performance_trends.iloc[idx]
            prev = self.performance_trends.iloc[idx-1]
            
            rating_change = curr['avg_rating'] - prev['avg_rating']
            std_change = curr['rating_std'] - prev['rating_std']
            
            # Detect significant transitions
            if abs(rating_change) > 0.2 or abs(std_change) > 0.3:
                transition_type = 'generosity_shift' if abs(rating_change) > 0.2 else 'consensus_shift'
                
                transitions.append({
                    'league_number': curr['league_number'],
                    'league_title': curr['league_title'],
                    'transition_type': transition_type,
                    'rating_change': rating_change,
                    'std_change': std_change,
                    'significance': 'major' if abs(rating_change) > 0.3 or abs(std_change) > 0.5 else 'moderate'
                })
        
        return pd.DataFrame(transitions)
    
    def generate_comprehensive_report(self, print_report=True):
        """Generate a comprehensive historical analysis report
        
        Args:
            print_report: If True, print the report to console. If False, just return data.
        """
        
        if print_report:
            print("="*80)
            print("      HISTORICAL PERFORMANCE PATTERN ANALYSIS")
            print("      Music League Preference Evolution Report")
            print("="*80)
        
        # Load all data
        self.load_chronological_data()
        voter_evolution = self.analyze_voter_pool_evolution()
        preference_trends = self.analyze_preference_evolution()
        impact_analysis = self.analyze_voter_impact_on_preferences()
        voter_classifications = self.identify_stable_core_vs_transient_voters()
        era_transitions = self.analyze_era_transitions()
        
        # If not printing, return data immediately
        if not print_report:
            return {
                'voter_evolution': voter_evolution,
                'preference_trends': preference_trends,
                'impact_analysis': impact_analysis,
                'voter_classifications': voter_classifications,
                'era_transitions': era_transitions
            }
        
        # Print the full report
        print(f"\nAnalyzed {len(self.leagues_data)} leagues spanning {self.leagues_data['league_number'].min()}-{self.leagues_data['league_number'].max()}")
        print(f"Total unique voters: {len(voter_classifications)}")
        print(f"Total songs analyzed: {self.leagues_data['song_count'].sum()}")
        print(f"Total votes analyzed: {self.leagues_data['total_votes'].sum()}")
        
        # Section 1: Voter Pool Evolution
        print(f"\n" + "-"*80)
        print("VOTER POOL EVOLUTION")
        print("-"*80)
        
        print(f"\nLeague Participation Overview:")
        print(f"  Average voters per league: {voter_evolution['total_voters'].mean():.1f}")
        print(f"  Peak participation: {voter_evolution['total_voters'].max()} voters")
        print(f"  Minimum participation: {voter_evolution['total_voters'].min()} voters")
        print(f"  Average turnover rate: {voter_evolution['voter_turnover_rate'].mean()*100:.1f}%")
        
        # High turnover periods
        high_turnover = voter_evolution[voter_evolution['voter_turnover_rate'] > 0.4]
        if not high_turnover.empty:
            print(f"\nHigh turnover periods (>40% new voters):")
            for _, period in high_turnover.iterrows():
                print(f"  {period['league_title']}: {period['voter_turnover_rate']*100:.1f}% turnover")
        
        # Section 2: Voter Classification
        print(f"\n" + "-"*80)
        print("VOTER CLASSIFICATION ANALYSIS")
        print("-"*80)
        
        core_voters = voter_classifications[voter_classifications['voter_type'] == 'core']
        regular_voters = voter_classifications[voter_classifications['voter_type'] == 'regular']
        transient_voters = voter_classifications[voter_classifications['voter_type'] == 'transient']
        
        print(f"\nCore Voters (70%+ participation): {len(core_voters)}")
        for _, voter in core_voters.iterrows():
            print(f"  {voter['voter']}: {voter['leagues_participated']} leagues, {voter['avg_score']:.2f} avg score")
        
        print(f"\nRegular Voters (30-70% participation): {len(regular_voters)}")
        for _, voter in regular_voters.head(5).iterrows():
            print(f"  {voter['voter']}: {voter['leagues_participated']} leagues, {voter['avg_score']:.2f} avg score")
        
        print(f"\nTransient Voters (<30% participation): {len(transient_voters)}")
        print(f"  Average participation: {transient_voters['leagues_participated'].mean():.1f} leagues")
        
        # Section 3: Preference Evolution
        print(f"\n" + "-"*80)
        print("GROUP PREFERENCE EVOLUTION")
        print("-"*80)
        
        print(f"\nScoring Generosity Trends:")
        early_leagues = preference_trends.head(5)['avg_rating'].mean()
        recent_leagues = preference_trends.tail(5)['avg_rating'].mean()
        generosity_change = recent_leagues - early_leagues
        
        print(f"  Early leagues (first 5): {early_leagues:.2f} average rating")
        print(f"  Recent leagues (last 5): {recent_leagues:.2f} average rating")
        print(f"  Overall trend: {'More generous' if generosity_change > 0.1 else 'More conservative' if generosity_change < -0.1 else 'Stable'}")
        print(f"  Change magnitude: {generosity_change:+.2f}")
        
        print(f"\nConsensus Evolution:")
        early_std = preference_trends.head(5)['rating_std'].mean()
        recent_std = preference_trends.tail(5)['rating_std'].mean()
        consensus_change = recent_std - early_std
        
        print(f"  Early disagreement: {early_std:.2f} standard deviation")
        print(f"  Recent disagreement: {recent_std:.2f} standard deviation")
        print(f"  Consensus trend: {'Less consensus' if consensus_change > 0.1 else 'More consensus' if consensus_change < -0.1 else 'Stable'}")
        
        # Section 4: Era Transitions
        if not era_transitions.empty:
            print(f"\n" + "-"*80)
            print("MAJOR ERA TRANSITIONS")
            print("-"*80)
            
            for _, transition in era_transitions.iterrows():
                print(f"\n{transition['league_title']} ({transition['significance']} {transition['transition_type']}):")
                if transition['transition_type'] == 'generosity_shift':
                    direction = 'more generous' if transition['rating_change'] > 0 else 'more conservative'
                    print(f"  Scoring became {direction} by {abs(transition['rating_change']):.2f} points")
                else:
                    direction = 'less consensus' if transition['std_change'] > 0 else 'more consensus'
                    print(f"  Group developed {direction} (std change: {transition['std_change']:+.2f})")
        
        # Section 5: Impact Analysis
        print(f"\n" + "-"*80)
        print("VOTER TURNOVER IMPACT ON PREFERENCES")
        print("-"*80)
        
        # Correlate turnover with preference changes
        positive_changes = impact_analysis[impact_analysis['impact_direction'] == 'positive']
        negative_changes = impact_analysis[impact_analysis['impact_direction'] == 'negative']
        
        if not positive_changes.empty:
            print(f"\nLeagues with increased generosity:")
            for _, change in positive_changes.iterrows():
                print(f"  {change['league_title']}: +{change['score_change']:.2f} (turnover: {change['turnover_rate']*100:.0f}%)")
        
        if not negative_changes.empty:
            print(f"\nLeagues with decreased generosity:")
            for _, change in negative_changes.iterrows():
                print(f"  {change['league_title']}: {change['score_change']:.2f} (turnover: {change['turnover_rate']*100:.0f}%)")
        
        # Section 6: Predictive Insights
        print(f"\n" + "-"*80)
        print("PREDICTIVE INSIGHTS FOR FUTURE LEAGUES")
        print("-"*80)
        
        # Current composition
        current_league = voter_evolution.iloc[-1]
        print(f"\nCurrent state (most recent league):")
        print(f"  Voters: {current_league['total_voters']}")
        print(f"  Average score: {current_league['avg_score']:.2f}")
        print(f"  Recent turnover: {current_league['voter_turnover_rate']*100:.0f}%")
        
        # Predict likely patterns
        avg_turnover = voter_evolution['voter_turnover_rate'].mean()
        if current_league['voter_turnover_rate'] > avg_turnover * 1.5:
            print(f"  Prediction: High turnover may lead to scoring pattern shift")
        elif current_league['voter_turnover_rate'] < avg_turnover * 0.5:
            print(f"  Prediction: Stable voter pool, consistent scoring expected")
        
        return {
            'voter_evolution': voter_evolution,
            'preference_trends': preference_trends,
            'impact_analysis': impact_analysis,
            'voter_classifications': voter_classifications,
            'era_transitions': era_transitions
        }

if __name__ == "__main__":
    analyzer = HistoricalPatternAnalyzer()
    results = analyzer.generate_comprehensive_report()
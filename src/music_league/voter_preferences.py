#!/usr/bin/env ./venv/bin/python3
"""
Voter Preference Modeling System
Builds preference profiles and implements collaborative filtering
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler

from music_league.setup_db import get_db_connection

logger = logging.getLogger(__name__)

@dataclass
class VoterProfile:
    """Profile of a voter's musical preferences"""
    voter_name: str
    total_votes: int
    avg_score: float
    score_distribution: Dict[int, int]  # point -> count
    top_artists: List[Tuple[str, float]]  # (artist, avg_score)
    top_genres: List[str]  # Inferred genres
    voting_generosity: float  # How generous with high scores
    consistency: float  # How consistent in scoring patterns
    activity_level: str  # "high", "medium", "low"

@dataclass
class SongPreference:
    """Predicted preference for a song"""
    song_title: str
    artist: str
    predicted_score: float
    confidence: float
    similar_voters: List[str]
    reasoning: str

class VoterPreferenceModeler:
    """Advanced voter preference modeling and collaborative filtering system"""
    
    def __init__(self):
        self.conn = get_db_connection()
        self.voter_profiles = {}
        self.voter_song_matrix = None
        self.voters = []
        self.songs = []
        self.similarity_matrix = None
        self.svd_model = None
        
        logger.info("Voter Preference Modeler initialized")
    
    def load_voting_data(self) -> pd.DataFrame:
        """Load all voting data into a DataFrame"""
        query = """
        SELECT 
            v.voter,
            v.song_id,
            v.points,
            s.title as song_title,
            s.artist,
            r.title as round_title,
            r.description as round_description
        FROM votes v
        JOIN songs s ON v.song_id = s.id
        JOIN rounds r ON s.round_id = r.id
        WHERE v.points IS NOT NULL AND v.points > 0
        ORDER BY v.voter, v.song_id
        """
        
        df = pd.read_sql_query(query, self.conn)
        logger.info(f"Loaded {len(df)} voting records")
        return df
    
    def build_voter_song_matrix(self, df: pd.DataFrame) -> np.ndarray:
        """Build voter-song interaction matrix"""
        
        # Get unique voters and songs
        self.voters = sorted(df['voter'].unique())
        self.songs = sorted(df['song_id'].unique())
        
        # Create matrix
        matrix = np.zeros((len(self.voters), len(self.songs)))
        
        # Fill matrix with scores
        for _, row in df.iterrows():
            voter_idx = self.voters.index(row['voter'])
            song_idx = self.songs.index(row['song_id'])
            matrix[voter_idx, song_idx] = row['points']
        
        self.voter_song_matrix = matrix
        logger.info(f"Built {matrix.shape} voter-song matrix with {np.count_nonzero(matrix)} interactions")
        return matrix
    
    def build_voter_profiles(self, df: pd.DataFrame) -> Dict[str, VoterProfile]:
        """Build comprehensive profiles for each voter"""
        
        profiles = {}
        
        for voter in self.voters:
            voter_data = df[df['voter'] == voter].copy()
            
            if len(voter_data) == 0:
                continue
            
            # Basic stats
            total_votes = len(voter_data)
            avg_score = voter_data['points'].mean()
            
            # Score distribution
            score_dist = voter_data['points'].value_counts().to_dict()
            
            # Top artists (by average score)
            artist_scores = voter_data.groupby('artist')['points'].agg(['mean', 'count']).reset_index()
            artist_scores = artist_scores[artist_scores['count'] >= 2]  # At least 2 votes
            top_artists = [(row['artist'], row['mean']) for _, row in 
                          artist_scores.nlargest(10, 'mean').iterrows()]
            
            # Voting generosity (tendency to give high scores)
            high_scores = len(voter_data[voter_data['points'] >= 3])
            generosity = high_scores / total_votes if total_votes > 0 else 0
            
            # Consistency (std deviation of scores - lower = more consistent)
            consistency = 1.0 / (voter_data['points'].std() + 0.1)  # Add small constant to avoid division by zero
            
            # Activity level
            if total_votes >= 500:
                activity = "high"
            elif total_votes >= 100:
                activity = "medium"
            else:
                activity = "low"
            
            # Create profile
            profile = VoterProfile(
                voter_name=voter,
                total_votes=total_votes,
                avg_score=avg_score,
                score_distribution=score_dist,
                top_artists=top_artists,
                top_genres=[],  # TODO: Implement genre inference
                voting_generosity=generosity,
                consistency=consistency,
                activity_level=activity
            )
            
            profiles[voter] = profile
        
        self.voter_profiles = profiles
        logger.info(f"Built profiles for {len(profiles)} voters")
        return profiles
    
    def calculate_voter_similarity(self) -> np.ndarray:
        """Calculate pairwise voter similarity using cosine similarity"""
        
        if self.voter_song_matrix is None:
            raise ValueError("Voter-song matrix not built. Call build_voter_song_matrix first.")
        
        # Use cosine similarity on the voter-song matrix
        similarity_matrix = cosine_similarity(self.voter_song_matrix)
        self.similarity_matrix = similarity_matrix
        
        logger.info(f"Calculated voter similarity matrix: {similarity_matrix.shape}")
        return similarity_matrix
    
    def find_similar_voters(self, voter: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find the most similar voters to a given voter"""
        
        if voter not in self.voters:
            return []
        
        voter_idx = self.voters.index(voter)
        similarities = self.similarity_matrix[voter_idx]
        
        # Get top-k similar voters (excluding self)
        similar_indices = np.argsort(similarities)[::-1][1:top_k+1]
        similar_voters = [(self.voters[idx], similarities[idx]) for idx in similar_indices]
        
        return similar_voters
    
    def predict_song_preference_collaborative(self, voter: str, song_id: str, 
                                           top_k_voters: int = 5) -> Optional[SongPreference]:
        """Predict a voter's preference for a song using collaborative filtering"""
        
        if voter not in self.voters or song_id not in self.songs:
            return None
        
        voter_idx = self.voters.index(voter)
        song_idx = self.songs.index(song_id)
        
        # If voter already rated this song, return actual rating
        actual_score = self.voter_song_matrix[voter_idx, song_idx]
        if actual_score > 0:
            return None  # Already rated
        
        # Find similar voters who rated this song
        similar_voters = self.find_similar_voters(voter, top_k=20)
        
        # Get ratings from similar voters for this song
        weighted_scores = []
        similar_voter_names = []
        
        for similar_voter, similarity in similar_voters:
            if similarity <= 0:  # Skip voters with negative or zero similarity
                continue
                
            similar_voter_idx = self.voters.index(similar_voter)
            similar_score = self.voter_song_matrix[similar_voter_idx, song_idx]
            
            if similar_score > 0:  # Similar voter rated this song
                weighted_scores.append(similar_score * similarity)
                similar_voter_names.append(similar_voter)
        
        if not weighted_scores:
            return None  # No similar voters rated this song
        
        # Calculate weighted average prediction
        predicted_score = np.mean(weighted_scores)
        
        # Calculate confidence based on number of similar voters and their similarity
        confidence = min(1.0, len(weighted_scores) / top_k_voters)
        
        # Get song info
        cursor = self.conn.cursor()
        cursor.execute("SELECT title, artist FROM songs WHERE id = ?", (song_id,))
        song_info = cursor.fetchone()
        
        if not song_info:
            return None
        
        reasoning = f"Based on {len(similar_voter_names)} similar voters' preferences"
        
        return SongPreference(
            song_title=song_info['title'],
            artist=song_info['artist'],
            predicted_score=predicted_score,
            confidence=confidence,
            similar_voters=similar_voter_names[:5],
            reasoning=reasoning
        )
    
    def predict_voter_preferences_for_candidates(self, voter: str, 
                                               candidate_songs: List[Dict]) -> List[SongPreference]:
        """Predict voter preferences for a list of candidate songs"""
        
        predictions = []
        
        for candidate in candidate_songs:
            # Try to find song in database
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id FROM songs 
                WHERE LOWER(title) LIKE LOWER(?) AND LOWER(artist) LIKE LOWER(?)
                LIMIT 1
            """, (f"%{candidate['title']}%", f"%{candidate['artist']}%"))
            
            result = cursor.fetchone()
            
            if result:
                # Song exists in database - use collaborative filtering
                song_id = result['id']
                prediction = self.predict_song_preference_collaborative(voter, song_id)
                if prediction:
                    predictions.append(prediction)
            else:
                # Song not in database - use profile-based prediction
                profile_prediction = self._predict_from_voter_profile(voter, candidate)
                if profile_prediction:
                    predictions.append(profile_prediction)
        
        return predictions
    
    def _predict_from_voter_profile(self, voter: str, candidate: Dict) -> Optional[SongPreference]:
        """Predict preference based on voter's profile patterns"""
        
        if voter not in self.voter_profiles:
            return None
        
        profile = self.voter_profiles[voter]
        
        # Check if voter has liked this artist before
        artist_score = None
        for artist, score in profile.top_artists:
            if artist.lower() in candidate['artist'].lower() or candidate['artist'].lower() in artist.lower():
                artist_score = score
                break
        
        if artist_score:
            # Artist familiarity bonus
            predicted_score = min(5.0, artist_score * 1.1)
            confidence = 0.7
            reasoning = f"Voter previously rated {candidate['artist']} highly (avg {artist_score:.2f})"
        else:
            # Use voter's average score as baseline
            predicted_score = profile.avg_score
            confidence = 0.3
            reasoning = f"Based on voter's average scoring pattern ({profile.avg_score:.2f})"
        
        return SongPreference(
            song_title=candidate['title'],
            artist=candidate['artist'],
            predicted_score=predicted_score,
            confidence=confidence,
            similar_voters=[],
            reasoning=reasoning
        )
    
    def get_voter_profile_summary(self, voter: str) -> Optional[Dict]:
        """Get a summary of a voter's profile"""
        
        if voter not in self.voter_profiles:
            return None
        
        profile = self.voter_profiles[voter]
        similar_voters = self.find_similar_voters(voter, top_k=3)
        
        return {
            'profile': asdict(profile),
            'similar_voters': similar_voters,
            'voting_stats': {
                'total_votes': profile.total_votes,
                'avg_score': profile.avg_score,
                'generosity': profile.voting_generosity,
                'consistency': profile.consistency
            }
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Demo the voter preference modeling system"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    modeler = VoterPreferenceModeler()
    
    try:
        print("🧠 VOTER PREFERENCE MODELING SYSTEM")
        print("=" * 50)
        print()
        
        # Load and process data
        print("📊 Loading voting data...")
        df = modeler.load_voting_data()
        
        print("🔧 Building voter-song matrix...")
        modeler.build_voter_song_matrix(df)
        
        print("👥 Building voter profiles...")
        modeler.build_voter_profiles(df)
        
        print("🤝 Calculating voter similarities...")
        modeler.calculate_voter_similarity()
        
        print("\n" + "="*50)
        print("VOTER PREFERENCE ANALYSIS")
        print("="*50)
        
        # Analyze a few active voters
        active_voters = ['Joe Hayward', 'Drew', 'Matt M']
        
        for voter in active_voters:
            if voter in modeler.voter_profiles:
                print(f"\n👤 VOTER: {voter}")
                print("-" * 30)
                
                summary = modeler.get_voter_profile_summary(voter)
                profile = summary['profile']
                
                print(f"Activity: {profile['total_votes']} votes ({profile['activity_level']})")
                print(f"Average score: {profile['avg_score']:.2f}")
                print(f"Generosity: {profile['voting_generosity']:.2f} (high scores ratio)")
                print(f"Consistency: {profile['consistency']:.2f}")
                
                print("\nTop artists:")
                for artist, score in profile['top_artists'][:3]:
                    print(f"  • {artist}: {score:.2f} avg")
                
                print("\nMost similar voters:")
                for similar_voter, similarity in summary['similar_voters']:
                    print(f"  • {similar_voter}: {similarity:.3f} similarity")
        
        print(f"\n✅ Voter preference modeling system ready!")
        print(f"   • {len(modeler.voter_profiles)} voter profiles built")
        print(f"   • {modeler.voter_song_matrix.shape} interaction matrix")
        print(f"   • Collaborative filtering enabled")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Error: {e}")
    finally:
        modeler.close()

if __name__ == "__main__":
    main()
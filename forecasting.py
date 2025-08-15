#!/usr/bin/env ./venv/bin/python3
"""
Music League Preference Forecasting System
Phase 1: LLM-Enhanced Theme Matching with Spotify Integration
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np
from anthropic import Anthropic
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

from config import DATABASE_PATH
from setup_db import get_db_connection
from audio_features_fallback import AudioFeatureEstimator, FallbackAudioFeatures

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class SongFeatures:
    """Audio features for a song from Spotify"""
    energy: float
    danceability: float
    valence: float
    acousticness: float
    instrumentalness: float
    liveness: float
    speechiness: float
    tempo: float
    loudness: float
    key: int
    mode: int
    time_signature: int

@dataclass
class ThemeAnalysis:
    """LLM analysis of a round theme"""
    emotional_tone: str
    musical_characteristics: List[str]
    genre_preferences: List[str]
    energy_level: str
    thematic_keywords: List[str]
    success_factors: List[str]

@dataclass
class SongMatch:
    """A song matched to a theme with scoring"""
    song_id: int
    title: str
    artist: str
    theme_match_score: float
    audio_feature_score: float
    combined_score: float
    reasoning: str

class MusicForecaster:
    """Phase 1: LLM-Enhanced Theme Matching System"""
    
    def __init__(self):
        # Initialize APIs
        self.anthropic_client = None
        if os.getenv('ANTHROPIC_API_KEY'):
            self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        self.spotify = None
        if os.getenv('SPOTIFY_CLIENT_ID') and os.getenv('SPOTIFY_CLIENT_SECRET'):
            client_credentials_manager = SpotifyClientCredentials(
                client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
            )
            self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Initialize database connection
        self.conn = get_db_connection()
        
        # Initialize ML components
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Initialize fallback audio features
        self.audio_estimator = AudioFeatureEstimator()
        
        logger.info("Music Forecaster initialized")

    def get_round_data(self, round_id: str) -> Dict[str, Any]:
        """Get complete round data including theme, songs, and voting history"""
        cursor = self.conn.cursor()
        
        # Get round info
        cursor.execute("""
            SELECT r.*, l.title as league_title
            FROM rounds r
            JOIN leagues l ON r.league_id = l.id
            WHERE r.id = ?
        """, (round_id,))
        round_info = cursor.fetchone()
        
        if not round_info:
            raise ValueError(f"Round {round_id} not found")
        
        # Get songs with votes
        cursor.execute("""
            SELECT 
                s.id, s.title, s.artist, s.album, s.submitter,
                s.total_votes_awarded, s.final_score, s.num_voters,
                s.spotify_url
            FROM songs s
            WHERE s.round_id = ?
            ORDER BY s.final_score DESC
        """, (round_id,))
        songs = [dict(row) for row in cursor.fetchall()]
        
        # Get individual votes for each song
        for song in songs:
            cursor.execute("""
                SELECT voter, points, comment
                FROM votes
                WHERE song_id = ?
                ORDER BY points DESC
            """, (song['id'],))
            song['votes'] = [dict(row) for row in cursor.fetchall()]
        
        return {
            'round_info': dict(round_info),
            'songs': songs
        }

    def analyze_theme_with_llm(self, theme_title: str, theme_description: str) -> ThemeAnalysis:
        """Use Claude to analyze round theme and predict successful song characteristics"""
        if not self.anthropic_client:
            logger.warning("Anthropic API not available, using fallback analysis")
            return self._fallback_theme_analysis(theme_title, theme_description)
        
        prompt = f"""
        Analyze this Music League round theme and predict what types of songs would be successful:

        Theme Title: {theme_title}
        Theme Description: {theme_description}

        Please analyze:
        1. The emotional tone/mood this theme suggests
        2. Musical characteristics that would fit (tempo, energy, genre elements)
        3. Specific genres that might work well
        4. Overall energy level (high/medium/low)
        5. Key thematic keywords for matching
        6. Success factors for song selection

        Respond in JSON format with these fields:
        - emotional_tone: string describing the mood
        - musical_characteristics: array of musical elements
        - genre_preferences: array of genres
        - energy_level: "high", "medium", or "low"
        - thematic_keywords: array of relevant keywords
        - success_factors: array of what makes songs succeed for this theme
        """
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Using Sonnet for sophisticated theme analysis
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Handle JSON wrapped in markdown code blocks
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find any JSON object
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    json_text = response_text
            
            analysis_json = json.loads(json_text)
            return ThemeAnalysis(**analysis_json)
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._fallback_theme_analysis(theme_title, theme_description)

    def _fallback_theme_analysis(self, theme_title: str, theme_description: str) -> ThemeAnalysis:
        """Fallback analysis when LLM is not available"""
        # Simple keyword-based analysis
        text = f"{theme_title} {theme_description}".lower()
        
        if any(word in text for word in ['happy', 'joy', 'dance', 'party', 'celebration']):
            emotional_tone = "upbeat and positive"
            energy_level = "high"
        elif any(word in text for word in ['sad', 'slow', 'melancholy', 'quiet', 'soft']):
            emotional_tone = "melancholic and introspective"
            energy_level = "low"
        else:
            emotional_tone = "balanced"
            energy_level = "medium"
        
        return ThemeAnalysis(
            emotional_tone=emotional_tone,
            musical_characteristics=["varied"],
            genre_preferences=["rock", "pop", "indie"],
            energy_level=energy_level,
            thematic_keywords=theme_title.lower().split(),
            success_factors=["theme relevance", "musical quality"]
        )

    def get_spotify_features(self, song_title: str, artist: str) -> Optional[SongFeatures]:
        """Get audio features from Spotify API with fallback to estimation"""
        
        # Try Spotify first if available
        if self.spotify:
            try:
                # Search for the song
                query = f"track:{song_title} artist:{artist}"
                results = self.spotify.search(q=query, type='track', limit=1)
                
                if not results['tracks']['items']:
                    # Try simplified search
                    query = f"{song_title} {artist}"
                    results = self.spotify.search(q=query, type='track', limit=1)
                
                if results['tracks']['items']:
                    track = results['tracks']['items'][0]
                    track_id = track['id']
                    
                    # Get audio features (spotipy expects a list of track IDs)
                    features = self.spotify.audio_features([track_id])[0]
                    if features:
                        logger.info(f"Got Spotify features for {song_title} by {artist}")
                        return SongFeatures(
                            energy=features['energy'],
                            danceability=features['danceability'],
                            valence=features['valence'],
                            acousticness=features['acousticness'],
                            instrumentalness=features['instrumentalness'],
                            liveness=features['liveness'],
                            speechiness=features['speechiness'],
                            tempo=features['tempo'],
                            loudness=features['loudness'],
                            key=features['key'],
                            mode=features['mode'],
                            time_signature=features['time_signature']
                        )
                
            except Exception as e:
                if "403" in str(e):
                    logger.warning(f"Spotify API restricted (403) - using fallback for {song_title}")
                else:
                    logger.error(f"Spotify API error for {song_title} by {artist}: {e}")
        
        # Fallback to estimation
        logger.info(f"Using estimated features for {song_title} by {artist}")
        fallback_features = self.audio_estimator.estimate_features(song_title, artist)
        
        if fallback_features:
            return SongFeatures(
                energy=fallback_features.energy,
                danceability=fallback_features.danceability,
                valence=fallback_features.valence,
                acousticness=fallback_features.acousticness,
                instrumentalness=fallback_features.instrumentalness,
                liveness=fallback_features.liveness,
                speechiness=fallback_features.speechiness,
                tempo=fallback_features.tempo,
                loudness=fallback_features.loudness,
                key=fallback_features.key,
                mode=fallback_features.mode,
                time_signature=fallback_features.time_signature
            )
        
        return None

    def calculate_theme_match_score(self, song_title: str, artist: str, theme_analysis: ThemeAnalysis) -> float:
        """Calculate how well a song matches the theme using comprehensive semantic analysis"""
        
        # Primary: Use comprehensive LLM semantic analysis when available
        if self.anthropic_client:
            return self._comprehensive_semantic_analysis(song_title, artist, theme_analysis)
        else:
            # Fallback: Use enhanced textual similarity without brittle keyword penalties
            return self._semantic_textual_matching(song_title, artist, theme_analysis)

    def _comprehensive_semantic_analysis(self, song_title: str, artist: str, theme_analysis: ThemeAnalysis) -> float:
        """Use advanced LLM analysis to comprehensively evaluate song-theme matching"""
        
        try:
            # Build comprehensive analysis prompt
            theme_context = f"""
Theme Requirements:
- Emotional tone: {theme_analysis.emotional_tone}
- Musical characteristics: {', '.join(theme_analysis.musical_characteristics)}
- Genre preferences: {', '.join(theme_analysis.genre_preferences)}
- Energy level: {theme_analysis.energy_level}
- Key thematic elements: {', '.join(theme_analysis.thematic_keywords)}
- Success factors: {', '.join(theme_analysis.success_factors)}
"""

            prompt = f"""As a music expert, analyze how well "{song_title}" by {artist} matches this Music League theme:

{theme_context}

Consider these factors holistically:

1. **Artist Genre & Style**: What genre(s) is {artist} known for? Do they match the theme's genre preferences?

2. **Song Title Semantics**: What does "{song_title}" suggest about the song's subject matter, mood, and thematic content?

3. **Musical Characteristics**: Based on the artist and song title, what would you expect for:
   - Energy level (high/medium/low)
   - Tempo and rhythm
   - Mood and emotional valence
   - Musical style and instrumentation

4. **Thematic Appropriateness**: How well does this song conceptually fit the theme requirements?

5. **Semantic vs. Surface Match**: Does this represent a genuine thematic match or just coincidental keyword overlap?

6. **Music League Context**: Would this be a smart, appropriate choice that demonstrates understanding of the theme?

Rate the overall match from 0.0 to 1.0, where:
- 0.9-1.0: Perfect thematic match, ideal choice
- 0.7-0.8: Strong match, very appropriate 
- 0.5-0.6: Decent fit, reasonable choice
- 0.3-0.4: Weak connection, questionable
- 0.0-0.2: Poor match, inappropriate

Respond with just the score (0.0-1.0) followed by a concise explanation of your reasoning."""

            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Using Sonnet for critical analysis
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Extract score with more robust parsing
            import re
            score_pattern = r'(?:^|\s)([0-1]\.?\d*|1\.0+)(?:\s|$)'
            score_match = re.search(score_pattern, response_text)
            
            if score_match:
                score = float(score_match.group(1))
                score = max(0.0, min(1.0, score))  # Ensure valid range
                
                logger.info(f"Comprehensive semantic analysis for {song_title}: {score:.3f}")
                return score
            else:
                # Try to find any decimal number
                decimal_match = re.search(r'(\d+\.?\d*)', response_text)
                if decimal_match:
                    score = float(decimal_match.group(1))
                    if score > 1.0:
                        score = score / 10.0  # Handle "8" -> "0.8" cases
                    score = max(0.0, min(1.0, score))
                    
                    logger.info(f"Parsed semantic analysis score for {song_title}: {score:.3f}")
                    return score
            
        except Exception as e:
            logger.warning(f"Comprehensive semantic analysis failed for {song_title}: {e}")
        
        # Fallback to semantic textual matching
        return self._semantic_textual_matching(song_title, artist, theme_analysis)

    def _semantic_textual_matching(self, song_title: str, artist: str, theme_analysis: ThemeAnalysis) -> float:
        """Semantic textual similarity without brittle keyword penalties"""
        song_text = f"{song_title} {artist}".lower()
        theme_text = " ".join([
            theme_analysis.emotional_tone,
            " ".join(theme_analysis.musical_characteristics),
            " ".join(theme_analysis.genre_preferences),
            " ".join(theme_analysis.thematic_keywords)
        ]).lower()
        
        # Use TF-IDF similarity as primary metric
        try:
            vectors = self.tfidf_vectorizer.fit_transform([song_text, theme_text])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            
            # Apply contextual weighting rather than hard penalties
            context_bonus = 0.0
            
            # Bonus for thematic keyword matches
            song_words = set(song_text.split())
            theme_keywords = set(theme_analysis.thematic_keywords)
            keyword_overlap = len(song_words.intersection(theme_keywords))
            if keyword_overlap > 0:
                context_bonus += min(0.2, keyword_overlap * 0.1)
            
            # Bonus for genre coherence (without penalties)
            genre_words = set([g.lower() for g in theme_analysis.genre_preferences])
            if song_words.intersection(genre_words):
                context_bonus += 0.1
            
            # Bonus for emotional tone alignment
            tone_words = set(theme_analysis.emotional_tone.lower().split())
            if song_words.intersection(tone_words):
                context_bonus += 0.1
            
            final_score = min(1.0, similarity + context_bonus)
            return final_score
            
        except:
            # Simple word overlap fallback without penalties
            song_words = set(song_text.split())
            theme_words = set(theme_text.split())
            overlap = len(song_words.intersection(theme_words))
            base_score = overlap / max(len(theme_words), 1)
            
            return min(1.0, base_score)

    def calculate_audio_feature_score(self, features: SongFeatures, theme_analysis: ThemeAnalysis) -> float:
        """Calculate score based on how well audio features match theme expectations"""
        if not features:
            return 0.5  # Neutral score when features unavailable
        
        score = 0.0
        
        # Energy level matching
        if theme_analysis.energy_level == "high":
            score += features.energy * 0.3 + features.danceability * 0.2
        elif theme_analysis.energy_level == "low":
            score += (1 - features.energy) * 0.3 + features.acousticness * 0.2
        else:  # medium
            score += (0.5 - abs(features.energy - 0.5)) * 0.3 + features.valence * 0.2
        
        # Emotional tone matching (using valence)
        if "positive" in theme_analysis.emotional_tone.lower():
            score += features.valence * 0.3
        elif "melancholic" in theme_analysis.emotional_tone.lower() or "sad" in theme_analysis.emotional_tone.lower():
            score += (1 - features.valence) * 0.3
        else:
            score += features.valence * 0.1  # Neutral contribution
        
        return min(score, 1.0)  # Cap at 1.0

    def filter_previous_submissions(self, candidate_songs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove songs that have already been submitted in previous rounds"""
        cursor = self.conn.cursor()
        
        filtered_songs = []
        for song in candidate_songs:
            # Check if this song (title + artist combo) already exists
            cursor.execute("""
                SELECT COUNT(*) as count FROM songs 
                WHERE LOWER(title) = LOWER(?) AND LOWER(artist) = LOWER(?)
            """, (song['title'], song['artist']))
            
            result = cursor.fetchone()
            if result['count'] == 0:
                filtered_songs.append(song)
            else:
                logger.info(f"Filtering out previous submission: {song['title']} by {song['artist']}")
        
        return filtered_songs

    def predict_song_success(self, round_id: str, candidate_songs: List[Dict[str, str]]) -> List[SongMatch]:
        """Predict how well candidate songs would perform in a given round"""
        round_data = self.get_round_data(round_id)
        round_info = round_data['round_info']
        
        # Analyze the theme
        theme_analysis = self.analyze_theme_with_llm(
            round_info['title'], 
            round_info.get('description', '')
        )
        
        logger.info(f"Theme analysis for '{round_info['title']}': {theme_analysis.emotional_tone}")
        
        matches = []
        for i, song in enumerate(candidate_songs):
            logger.info(f"Analyzing candidate song {i+1}/{len(candidate_songs)}: {song['title']} by {song['artist']}")
            
            # Calculate theme match score
            theme_score = self.calculate_theme_match_score(
                song['title'], song['artist'], theme_analysis
            )
            
            # Get Spotify features and calculate audio score
            spotify_features = self.get_spotify_features(song['title'], song['artist'])
            audio_score = self.calculate_audio_feature_score(spotify_features, theme_analysis)
            
            # Combined score (weighted average)
            combined_score = theme_score * 0.6 + audio_score * 0.4
            
            # Generate reasoning
            reasoning = f"Theme match: {theme_score:.2f}, Audio features: {audio_score:.2f}"
            if spotify_features:
                reasoning += f" (Energy: {spotify_features.energy:.2f}, Valence: {spotify_features.valence:.2f})"
            
            matches.append(SongMatch(
                song_id=i,
                title=song['title'],
                artist=song['artist'],
                theme_match_score=theme_score,
                audio_feature_score=audio_score,
                combined_score=combined_score,
                reasoning=reasoning
            ))
        
        # Sort by combined score (descending)
        matches.sort(key=lambda x: x.combined_score, reverse=True)
        return matches

    def evaluate_historical_accuracy(self, round_id: str) -> Dict[str, float]:
        """Evaluate how well our predictions match actual historical results"""
        round_data = self.get_round_data(round_id)
        songs = round_data['songs']
        
        if len(songs) < 2:
            return {"error": "Not enough songs to evaluate"}
        
        # Convert to candidate format
        candidates = [{"title": s['title'], "artist": s['artist']} for s in songs]
        
        # Get predictions
        predictions = self.predict_song_success(round_id, candidates)
        
        # Calculate correlation with actual scores
        predicted_scores = [p.combined_score for p in predictions]
        actual_scores = [s['final_score'] for s in songs]
        
        correlation = np.corrcoef(predicted_scores, actual_scores)[0, 1]
        if np.isnan(correlation):
            correlation = 0.0
        
        return {
            "correlation": correlation,
            "predictions": len(predictions),
            "actual_songs": len(songs)
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Demo the forecasting system"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    forecaster = MusicForecaster()
    
    try:
        # Get a sample round for testing
        cursor = forecaster.conn.cursor()
        cursor.execute("SELECT id, title FROM rounds ORDER BY RANDOM() LIMIT 1")
        round_info = cursor.fetchone()
        
        if not round_info:
            print("No rounds found in database. Run scraper.py first.")
            return
        
        round_id = round_info['id']
        round_title = round_info['title']
        
        print(f"\nTesting forecasting system with round: '{round_title}'")
        print("=" * 60)
        
        # Evaluate historical accuracy
        accuracy = forecaster.evaluate_historical_accuracy(round_id)
        print(f"\nHistorical accuracy evaluation:")
        print(f"Correlation with actual results: {accuracy.get('correlation', 0):.3f}")
        
        # Test with some candidate songs
        test_candidates = [
            {"title": "Bohemian Rhapsody", "artist": "Queen"},
            {"title": "Smells Like Teen Spirit", "artist": "Nirvana"},
            {"title": "Hotel California", "artist": "Eagles"}
        ]
        
        print(f"\nTesting predictions for candidate songs:")
        predictions = forecaster.predict_song_success(round_id, test_candidates)
        
        for i, pred in enumerate(predictions, 1):
            print(f"{i}. {pred.title} by {pred.artist}")
            print(f"   Combined Score: {pred.combined_score:.3f}")
            print(f"   Reasoning: {pred.reasoning}")
            print()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Error: {e}")
        
    finally:
        forecaster.close()

if __name__ == "__main__":
    main()
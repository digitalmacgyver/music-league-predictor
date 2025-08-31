#!/usr/bin/env ./venv/bin/python3
"""
Enhanced Music League Forecasting with Ensemble Models

Integrates ensemble prediction models into the forecasting system
for more accurate and robust song recommendations.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from forecasting import MusicForecaster, SongMatch, ThemeAnalysis
from ensemble_models import (
    EnsembleManager, PredictionComponent, EnsemblePrediction,
    WeightedEnsemble, StackedEnsemble, DynamicWeightedEnsemble, VotingEnsemble
)
from music_league.setup_db import get_db_connection

logger = logging.getLogger(__name__)

@dataclass
class EnhancedSongMatch:
    """Enhanced song match with ensemble prediction details"""
    song_id: int
    title: str
    artist: str
    theme_match_score: float
    audio_feature_score: float
    voter_preference_score: float = 0.0
    historical_adjustment: float = 1.0
    lyrical_score: float = 0.0
    ensemble_score: float = 0.0
    ensemble_confidence: float = 0.0
    ensemble_method: str = ""
    component_breakdown: List[PredictionComponent] = None
    reasoning: str = ""

class EnsembleForecaster:
    """Enhanced forecaster using ensemble models for predictions"""
    
    def __init__(self, enable_ensemble_training: bool = True):
        self.base_forecaster = MusicForecaster()
        self.ensemble_manager = EnsembleManager()
        self.enable_ensemble_training = enable_ensemble_training
        self.is_ensemble_trained = False
        
        # Training data for ensemble models
        self.training_predictions = []
        self.training_targets = []
        
    def close(self):
        """Clean up resources"""
        if self.base_forecaster:
            self.base_forecaster.close()
    
    def load_historical_training_data(self, min_samples: int = 50) -> bool:
        """Load historical song performance data for ensemble training"""
        
        if not self.enable_ensemble_training:
            return False
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get historical songs with good performance data
            cursor.execute("""
                SELECT s.title, s.artist, s.final_score, r.title as round_title, 
                       r.description as round_description, s.total_votes_awarded,
                       s.num_voters
                FROM songs s
                JOIN rounds r ON s.round_id = r.id
                WHERE s.final_score > 0 AND s.num_voters >= 5
                ORDER BY RANDOM()
                LIMIT ?
            """, (min_samples * 2,))  # Get extra samples in case some fail
            
            historical_songs = cursor.fetchall()
            conn.close()
            
            if len(historical_songs) < min_samples:
                logger.warning(f"Only found {len(historical_songs)} historical songs, need {min_samples}")
                return False
            
            logger.info(f"Loading ensemble training data from {len(historical_songs)} historical songs...")
            
            # Generate predictions for historical songs
            successful_predictions = 0
            
            for song in historical_songs:
                try:
                    # Create theme analysis for this round
                    theme_analysis = ThemeAnalysis(
                        theme=song['round_title'],
                        description=song['round_description'] or "",
                        key_concepts=[],
                        mood_descriptors=[],
                        audio_preferences={}
                    )
                    
                    # Get individual component scores
                    theme_score = self.base_forecaster.calculate_theme_match_score(
                        song['title'], song['artist'], theme_analysis
                    )
                    
                    spotify_features = self.base_forecaster.get_spotify_features(
                        song['title'], song['artist']
                    )
                    audio_score = self.base_forecaster.calculate_audio_feature_score(
                        spotify_features, theme_analysis
                    )
                    
                    # Create prediction components
                    components = [
                        PredictionComponent("theme_match", theme_score, 0.8, "Historical theme analysis"),
                        PredictionComponent("audio_features", audio_score, 0.7, "Historical audio analysis"),
                        PredictionComponent("baseline", 0.5, 0.5, "Baseline prediction")
                    ]
                    
                    # Normalize target score (final_score is typically 0-25, normalize to 0-1)
                    target_score = min(1.0, song['final_score'] / 25.0)
                    
                    self.training_predictions.append(components)
                    self.training_targets.append(target_score)
                    successful_predictions += 1
                    
                    if successful_predictions >= min_samples:
                        break
                        
                except Exception as e:
                    logger.debug(f"Failed to process historical song {song['title']}: {e}")
                    continue
            
            logger.info(f"Successfully prepared {successful_predictions} training examples")
            return successful_predictions >= min_samples
            
        except Exception as e:
            logger.error(f"Failed to load historical training data: {e}")
            return False
    
    def train_ensemble_models(self) -> bool:
        """Train ensemble models on historical data"""
        
        if self.is_ensemble_trained:
            return True
        
        if not self.training_predictions or len(self.training_predictions) < 10:
            # Try to load training data
            if not self.load_historical_training_data():
                logger.warning("Cannot train ensemble models - insufficient historical data")
                return False
        
        try:
            logger.info(f"Training ensemble models on {len(self.training_predictions)} examples...")
            self.ensemble_manager.train_all_models(self.training_predictions, self.training_targets)
            self.is_ensemble_trained = True
            
            # Log model performance
            rankings = self.ensemble_manager.get_model_rankings()
            logger.info("Ensemble model rankings:")
            for i, (name, perf) in enumerate(rankings[:3]):
                logger.info(f"  {i+1}. {name}: RMSE={perf['rmse']:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to train ensemble models: {e}")
            return False
    
    def predict_song_performance(self, song_title: str, artist: str, theme_analysis: ThemeAnalysis,
                                voter_preference_score: float = 0.0, 
                                historical_adjustment: float = 1.0,
                                theme_title: str = "", theme_description: str = "") -> EnhancedSongMatch:
        """Predict song performance using ensemble models"""
        
        try:
            # Get individual component predictions
            theme_score = self.base_forecaster.calculate_theme_match_score(
                song_title, artist, theme_analysis
            )
            
            spotify_features = self.base_forecaster.get_spotify_features(song_title, artist)
            audio_score = self.base_forecaster.calculate_audio_feature_score(
                spotify_features, theme_analysis
            )
            
            # Get lyrical analysis
            lyrical_score = 0.0
            if self.base_forecaster.lyrics_analyzer and theme_title:
                lyrical_score, _ = self.base_forecaster.calculate_lyrical_theme_score(
                    song_title, artist, theme_title, theme_description
                )
            
            # Create prediction components
            components = [
                PredictionComponent("theme_match", theme_score, 0.8, f"Theme relevance: {theme_score:.2f}"),
                PredictionComponent("audio_features", audio_score, 0.7, f"Audio alignment: {audio_score:.2f}")
            ]
            
            # Add lyrical analysis if available
            if lyrical_score > 0:
                components.append(
                    PredictionComponent("lyrical_match", lyrical_score, 0.9, f"Lyrical relevance: {lyrical_score:.2f}")
                )
            
            # Add voter preference if available
            if voter_preference_score > 0:
                components.append(
                    PredictionComponent("voter_preference", voter_preference_score, 0.9, 
                                      f"Voter compatibility: {voter_preference_score:.2f}")
                )
            
            # Add historical adjustment
            if abs(historical_adjustment - 1.0) > 0.05:
                components.append(
                    PredictionComponent("historical", historical_adjustment, 0.6,
                                      f"Group tendency adjustment: {historical_adjustment:.2f}")
                )
            
            # Get ensemble prediction
            if self.is_ensemble_trained:
                ensemble_pred = self.ensemble_manager.predict(components)
                ensemble_score = ensemble_pred.final_score
                ensemble_confidence = ensemble_pred.confidence
                ensemble_method = ensemble_pred.ensemble_method
                reasoning = ensemble_pred.reasoning
            else:
                # Fallback to weighted average
                weights = [0.4, 0.3, 0.2, 0.1]  # theme, audio, voter, historical
                weighted_scores = []
                for i, comp in enumerate(components):
                    weight = weights[i] if i < len(weights) else 0.1
                    weighted_scores.append(comp.score * weight)
                
                ensemble_score = sum(weighted_scores)
                ensemble_confidence = 0.5
                ensemble_method = "SimpleWeightedAverage"
                reasoning = "Ensemble not trained - using simple weighted average"
            
            return EnhancedSongMatch(
                song_id=0,  # Will be set by caller
                title=song_title,
                artist=artist,
                theme_match_score=theme_score,
                audio_feature_score=audio_score,
                voter_preference_score=voter_preference_score,
                historical_adjustment=historical_adjustment,
                lyrical_score=lyrical_score,
                ensemble_score=ensemble_score,
                ensemble_confidence=ensemble_confidence,
                ensemble_method=ensemble_method,
                component_breakdown=components,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Failed to predict performance for {song_title} by {artist}: {e}")
            # Return basic prediction
            return EnhancedSongMatch(
                song_id=0,
                title=song_title,
                artist=artist,
                theme_match_score=0.5,
                audio_feature_score=0.5,
                ensemble_score=0.5,
                ensemble_confidence=0.1,
                ensemble_method="Fallback",
                reasoning=f"Prediction failed: {str(e)}"
            )
    
    def predict_song_list(self, songs: List[Dict[str, str]], theme: str, description: str = "",
                         voter_preference_scores: Dict[str, float] = None,
                         historical_adjustment: float = 1.0) -> List[EnhancedSongMatch]:
        """Predict performance for a list of songs"""
        
        # Analyze theme first
        theme_analysis = self.base_forecaster.analyze_theme_with_llm(theme, description)
        
        predictions = []
        voter_scores = voter_preference_scores or {}
        
        for i, song in enumerate(songs):
            song_title = song.get('title', '')
            artist = song.get('artist', '')
            
            # Get voter preference score for this song
            song_key = f"{song_title.lower()}_{artist.lower()}"
            voter_score = voter_scores.get(song_key, 0.0)
            
            prediction = self.predict_song_performance(
                song_title, artist, theme_analysis, voter_score, historical_adjustment,
                theme, description
            )
            prediction.song_id = i
            predictions.append(prediction)
        
        # Sort by ensemble score
        predictions.sort(key=lambda x: x.ensemble_score, reverse=True)
        
        return predictions
    
    def train_and_predict(self, songs: List[Dict[str, str]], theme: str, description: str = "",
                         auto_train: bool = True) -> List[EnhancedSongMatch]:
        """Train ensemble models (if needed) and make predictions"""
        
        if auto_train and not self.is_ensemble_trained:
            self.train_ensemble_models()
        
        return self.predict_song_list(songs, theme, description)

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Test ensemble forecaster
    forecaster = EnsembleForecaster()
    
    # Example songs
    test_songs = [
        {"title": "Bohemian Rhapsody", "artist": "Queen"},
        {"title": "Stairway to Heaven", "artist": "Led Zeppelin"},
        {"title": "Hotel California", "artist": "Eagles"}
    ]
    
    # Make predictions
    predictions = forecaster.train_and_predict(
        test_songs, 
        "Epic rock anthems", 
        "Songs that build to an epic climax"
    )
    
    print("\nEnsemble Predictions:")
    for pred in predictions:
        print(f"{pred.title} by {pred.artist}:")
        print(f"  Ensemble Score: {pred.ensemble_score:.3f} (confidence: {pred.ensemble_confidence:.2f})")
        print(f"  Method: {pred.ensemble_method}")
        print(f"  Components: theme={pred.theme_match_score:.2f}, audio={pred.audio_feature_score:.2f}")
        print(f"  Reasoning: {pred.reasoning}")
        print()
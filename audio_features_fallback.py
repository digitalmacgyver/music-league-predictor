#!/usr/bin/env ./venv/bin/python3
"""
Alternative audio features provider when Spotify API is restricted
Uses music metadata and heuristics
"""

import re
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class FallbackAudioFeatures:
    """Audio features estimated from song metadata and heuristics"""
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
    confidence: float  # How confident we are in these estimates

class AudioFeatureEstimator:
    """Estimate audio features from song/artist information"""
    
    def __init__(self):
        # Genre-based feature templates
        self.genre_features = {
            'rock': {'energy': 0.8, 'danceability': 0.6, 'valence': 0.7, 'acousticness': 0.2},
            'pop': {'energy': 0.7, 'danceability': 0.8, 'valence': 0.8, 'acousticness': 0.3},
            'country': {'energy': 0.6, 'danceability': 0.5, 'valence': 0.6, 'acousticness': 0.6},
            'jazz': {'energy': 0.4, 'danceability': 0.4, 'valence': 0.5, 'acousticness': 0.7},
            'classical': {'energy': 0.3, 'danceability': 0.2, 'valence': 0.5, 'acousticness': 0.9},
            'hip-hop': {'energy': 0.8, 'danceability': 0.9, 'valence': 0.6, 'acousticness': 0.1},
            'electronic': {'energy': 0.9, 'danceability': 0.9, 'valence': 0.7, 'acousticness': 0.1},
            'folk': {'energy': 0.4, 'danceability': 0.3, 'valence': 0.6, 'acousticness': 0.8},
            'blues': {'energy': 0.5, 'danceability': 0.4, 'valence': 0.4, 'acousticness': 0.5},
            'reggae': {'energy': 0.6, 'danceability': 0.8, 'valence': 0.8, 'acousticness': 0.3}
        }
        
        # Artist-specific adjustments
        self.artist_adjustments = {
            'the beatles': {'energy': 0.7, 'valence': 0.8, 'acousticness': 0.4},
            'led zeppelin': {'energy': 0.9, 'valence': 0.7, 'acousticness': 0.2},
            'taylor swift': {'energy': 0.7, 'valence': 0.7, 'acousticness': 0.3},
            'bob dylan': {'energy': 0.5, 'valence': 0.6, 'acousticness': 0.7},
            'nirvana': {'energy': 0.9, 'valence': 0.4, 'acousticness': 0.2},
            'adele': {'energy': 0.5, 'valence': 0.4, 'acousticness': 0.6},
            'queen': {'energy': 0.8, 'valence': 0.8, 'acousticness': 0.3},
            'johnny cash': {'energy': 0.6, 'valence': 0.5, 'acousticness': 0.6},
            'radiohead': {'energy': 0.6, 'valence': 0.3, 'acousticness': 0.4},
            'beyoncé': {'energy': 0.8, 'valence': 0.8, 'acousticness': 0.2}
        }
        
        # Title-based mood detection
        self.positive_words = ['love', 'happy', 'joy', 'dance', 'party', 'celebration', 'good', 'better', 'best', 'amazing', 'wonderful']
        self.negative_words = ['sad', 'cry', 'tears', 'broken', 'hurt', 'pain', 'goodbye', 'lost', 'alone', 'dark']
        self.high_energy_words = ['rock', 'power', 'thunder', 'fire', 'electric', 'wild', 'crazy', 'loud', 'fast']
        self.low_energy_words = ['slow', 'quiet', 'soft', 'gentle', 'calm', 'peaceful', 'sleep', 'dream']

    def estimate_features(self, song_title: str, artist: str) -> Optional[FallbackAudioFeatures]:
        """Estimate audio features for a song"""
        
        song_lower = song_title.lower()
        artist_lower = artist.lower()
        
        # Start with default values
        features = {
            'energy': 0.6,
            'danceability': 0.6,
            'valence': 0.6,
            'acousticness': 0.4,
            'instrumentalness': 0.1,
            'liveness': 0.1,
            'speechiness': 0.1,
            'tempo': 120.0,
            'loudness': -8.0,
            'key': 5,
            'mode': 1,
            'time_signature': 4
        }
        
        confidence = 0.3  # Low confidence by default
        
        # Apply artist-specific adjustments
        for known_artist, adjustments in self.artist_adjustments.items():
            if known_artist in artist_lower:
                for feature, value in adjustments.items():
                    features[feature] = value
                confidence = 0.6
                break
        
        # Apply genre detection (basic)
        detected_genre = self._detect_genre(song_title, artist)
        if detected_genre:
            genre_features = self.genre_features[detected_genre]
            for feature, value in genre_features.items():
                features[feature] = (features[feature] + value) / 2  # Average with existing
            confidence = max(confidence, 0.5)
        
        # Apply title-based mood detection
        mood_adjustment = self._analyze_title_mood(song_title)
        if mood_adjustment:
            for feature, adjustment in mood_adjustment.items():
                features[feature] = max(0.0, min(1.0, features[feature] + adjustment))
            confidence = max(confidence, 0.4)
        
        return FallbackAudioFeatures(
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
            time_signature=features['time_signature'],
            confidence=confidence
        )
    
    def _detect_genre(self, song_title: str, artist: str) -> Optional[str]:
        """Basic genre detection from artist name"""
        artist_lower = artist.lower()
        
        # Rock artists
        rock_artists = ['led zeppelin', 'queen', 'the beatles', 'rolling stones', 'ac/dc', 'nirvana', 'foo fighters']
        if any(rock_artist in artist_lower for rock_artist in rock_artists):
            return 'rock'
        
        # Pop artists
        pop_artists = ['taylor swift', 'ariana grande', 'ed sheeran', 'dua lipa', 'harry styles']
        if any(pop_artist in artist_lower for pop_artist in pop_artists):
            return 'pop'
        
        # Country artists
        country_artists = ['johnny cash', 'dolly parton', 'keith urban', 'carrie underwood']
        if any(country_artist in artist_lower for country_artist in country_artists):
            return 'country'
        
        return None
    
    def _analyze_title_mood(self, song_title: str) -> Optional[Dict[str, float]]:
        """Analyze song title for mood indicators"""
        title_lower = song_title.lower()
        adjustments = {}
        
        # Check for positive words
        positive_count = sum(1 for word in self.positive_words if word in title_lower)
        if positive_count > 0:
            adjustments['valence'] = 0.2 * positive_count
            adjustments['energy'] = 0.1 * positive_count
        
        # Check for negative words
        negative_count = sum(1 for word in self.negative_words if word in title_lower)
        if negative_count > 0:
            adjustments['valence'] = -0.2 * negative_count
            adjustments['energy'] = -0.1 * negative_count
        
        # Check for energy words
        high_energy_count = sum(1 for word in self.high_energy_words if word in title_lower)
        if high_energy_count > 0:
            adjustments['energy'] = adjustments.get('energy', 0) + 0.2 * high_energy_count
            adjustments['danceability'] = 0.1 * high_energy_count
        
        low_energy_count = sum(1 for word in self.low_energy_words if word in title_lower)
        if low_energy_count > 0:
            adjustments['energy'] = adjustments.get('energy', 0) - 0.2 * low_energy_count
            adjustments['acousticness'] = 0.2 * low_energy_count
        
        return adjustments if adjustments else None

def main():
    """Test the fallback system"""
    estimator = AudioFeatureEstimator()
    
    test_songs = [
        ("Bohemian Rhapsody", "Queen"),
        ("Come Together", "The Beatles"), 
        ("Smells Like Teen Spirit", "Nirvana"),
        ("Hello", "Adele"),
        ("Happy", "Pharrell Williams"),
        ("Sad Song", "Unknown Artist")
    ]
    
    print("🎵 FALLBACK AUDIO FEATURES TEST")
    print("=" * 50)
    
    for title, artist in test_songs:
        features = estimator.estimate_features(title, artist)
        print(f"\n{title} by {artist}")
        print(f"  Energy: {features.energy:.2f}")
        print(f"  Valence: {features.valence:.2f}")
        print(f"  Danceability: {features.danceability:.2f}")
        print(f"  Confidence: {features.confidence:.2f}")

if __name__ == "__main__":
    main()
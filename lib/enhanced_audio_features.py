#!/usr/bin/env ./venv/bin/python3
"""
Enhanced Audio Features System

Replaces deprecated Spotify audio features with multi-tier approach:
1. Historical dataset lookup (170k tracks 1921-2020)
2. Essentia local analysis (when available)
3. Enhanced estimation fallback
"""

import sqlite3
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import re
from pathlib import Path

from setup_db import get_db_connection

logger = logging.getLogger(__name__)

@dataclass
class EnhancedAudioFeatures:
    """Enhanced audio features with source tracking"""
    # Core Spotify-compatible features
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
    time_signature: int = 4
    
    # Source tracking
    source: str = "estimation"  # "historical", "essentia", "estimation"
    confidence: float = 0.5
    
    # Additional metadata
    year: Optional[int] = None
    popularity: Optional[int] = None

class EnhancedAudioFeaturesProvider:
    """Multi-tier audio features provider"""
    
    def __init__(self, db_path: str = "audio_features.db"):
        self.db_path = db_path
        self.conn = None
        self.stats = {
            "historical_hits": 0,
            "essentia_analysis": 0,
            "estimation_fallback": 0,
            "total_requests": 0
        }
        
    def connect(self):
        """Connect to audio features database"""
        if Path(self.db_path).exists():
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to audio features database: {self.db_path}")
        else:
            logger.warning(f"Audio features database not found: {self.db_path}")
            logger.info("Run ./setup_audio_features_db.py to create it")
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for matching (same as setup script)"""
        if not text:
            return ""
        
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common words
        remove_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = text.split()
        words = [w for w in words if w not in remove_words]
        
        return ' '.join(words)
    
    def lookup_historical_features(self, title: str, artist: str) -> Optional[EnhancedAudioFeatures]:
        """Tier 1: Look up audio features from historical dataset"""
        if not self.conn:
            self.connect()
        
        if not self.conn:
            return None
        
        # Normalize inputs
        title_norm = self.normalize_text(title)
        artist_norm = self.normalize_text(artist)
        search_key = f"{title_norm} {artist_norm}".strip()
        
        cursor = self.conn.cursor()
        
        # Try exact search key match first
        cursor.execute("""
            SELECT * FROM historical_audio_features 
            WHERE search_key = ? 
            LIMIT 1
        """, (search_key,))
        
        result = cursor.fetchone()
        
        if not result:
            # Try fuzzy matching on title and artist separately
            cursor.execute("""
                SELECT * FROM historical_audio_features 
                WHERE title_normalized LIKE ? AND artist_normalized LIKE ?
                ORDER BY 
                    CASE 
                        WHEN title_normalized = ? AND artist_normalized = ? THEN 1
                        WHEN title_normalized = ? THEN 2
                        WHEN artist_normalized = ? THEN 3
                        ELSE 4
                    END
                LIMIT 1
            """, (f"%{title_norm}%", f"%{artist_norm}%", title_norm, artist_norm, title_norm, artist_norm))
            
            result = cursor.fetchone()
        
        if result:
            logger.info(f"✅ Historical match: {result['title']} by {result['artist']} ({result['year']})")
            
            return EnhancedAudioFeatures(
                energy=result['energy'],
                danceability=result['danceability'],
                valence=result['valence'],
                acousticness=result['acousticness'],
                instrumentalness=result['instrumentalness'],
                liveness=result['liveness'],
                speechiness=result['speechiness'],
                tempo=result['tempo'],
                loudness=result['loudness'],
                key=result['key'],
                mode=result['mode'],
                source="historical",
                confidence=0.9,  # High confidence for exact matches
                year=result['year'],
                popularity=result['popularity']
            )
        
        return None
    
    def analyze_with_essentia(self, title: str, artist: str, audio_file_path: Optional[str] = None) -> Optional[EnhancedAudioFeatures]:
        """Tier 2: Analyze audio with Essentia (requires audio file)"""
        if not audio_file_path:
            # No audio file provided - would need YouTube-DL or similar
            logger.debug(f"No audio file for Essentia analysis: {title} by {artist}")
            return None
        
        try:
            import essentia.standard as es
            import numpy as np
            
            # Load audio file
            loader = es.MonoLoader(filename=audio_file_path)
            audio = loader()
            
            logger.info(f"🎵 Analyzing with Essentia: {title} by {artist}")
            
            # Extract features using Essentia
            features = self._extract_essentia_features(audio)
            
            return EnhancedAudioFeatures(
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
                source="essentia",
                confidence=0.8  # High confidence for real analysis
            )
            
        except ImportError:
            logger.warning("Essentia not available")
            return None
        except Exception as e:
            logger.warning(f"Essentia analysis failed for {title} by {artist}: {e}")
            return None
    
    def _extract_essentia_features(self, audio) -> Dict[str, float]:
        """Extract Spotify-compatible features using Essentia"""
        import essentia.standard as es
        import numpy as np
        
        # Initialize algorithms
        windowing = es.Windowing(type='hann')
        spectrum = es.Spectrum()
        
        # Key and tempo analysis
        key_extractor = es.KeyExtractor()
        key, scale, strength = key_extractor(audio)
        
        # Convert key to Spotify format (0-11)
        key_mapping = {
            'A': 9, 'A#': 10, 'B': 11, 'C': 0, 'C#': 1, 'D': 2,
            'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8
        }
        spotify_key = key_mapping.get(key, 0)
        spotify_mode = 1 if scale == 'major' else 0
        
        # Frame-based analysis
        frame_size = 2048
        hop_size = 1024
        
        # Collect frame-based features
        energies = []
        zcr_values = []
        rolloff_values = []
        spectral_centroids = []
        
        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            windowed = windowing(frame)
            spec = spectrum(windowed)
            
            # Energy (RMS)
            energies.append(np.sqrt(np.mean(frame**2)))
            
            # Zero crossing rate
            zcr = es.ZeroCrossingRate()
            zcr_values.append(zcr(frame))
            
            # Spectral rolloff
            rolloff = es.RollOff()
            rolloff_values.append(rolloff(spec))
            
            # Spectral centroid (approximate)
            freqs = np.fft.fftfreq(len(spec), 1/44100)[:len(spec)]
            spectral_centroids.append(np.sum(freqs * spec) / np.sum(spec) if np.sum(spec) > 0 else 0)
        
        # Aggregate statistics
        mean_energy = np.mean(energies) if energies else 0.5
        mean_zcr = np.mean(zcr_values) if zcr_values else 0.1
        mean_rolloff = np.mean(rolloff_values) if rolloff_values else 2000
        mean_centroid = np.mean(spectral_centroids) if spectral_centroids else 1000
        
        # Loudness
        loudness_extractor = es.Loudness()
        loudness = loudness_extractor(audio)
        spotify_loudness = -60 + (loudness / 1000) * 50  # Approximate mapping
        
        # Map to Spotify-like features
        # These are rough approximations based on Essentia outputs
        features = {
            'energy': min(1.0, mean_energy * 2),  # Normalize energy
            'danceability': min(1.0, max(0.0, 0.5 + (mean_zcr - 0.1) * 2)),  # ZCR correlation
            'valence': min(1.0, max(0.0, mean_centroid / 3000)),  # Brightness correlation
            'acousticness': min(1.0, max(0.0, 1.0 - (mean_rolloff / 4000))),  # Inverse rolloff
            'instrumentalness': min(1.0, max(0.0, 1.0 - mean_zcr * 10)),  # Less variation = more instrumental
            'liveness': min(1.0, max(0.0, np.std(energies) if energies else 0.1)),  # Energy variation
            'speechiness': min(1.0, max(0.0, mean_zcr * 5)),  # ZCR correlation
            'tempo': 120.0,  # Would need beat tracking - default for now
            'loudness': max(-60, min(0, spotify_loudness)),
            'key': spotify_key,
            'mode': spotify_mode
        }
        
        return features
    
    def estimate_features(self, title: str, artist: str) -> EnhancedAudioFeatures:
        """Tier 3: Enhanced estimation based on genre, era, patterns"""
        # Enhanced estimation logic (improved from existing system)
        
        # Base defaults
        features = {
            'energy': 0.5,
            'danceability': 0.5,
            'valence': 0.5,
            'acousticness': 0.5,
            'instrumentalness': 0.05,
            'liveness': 0.1,
            'speechiness': 0.05,
            'tempo': 120.0,
            'loudness': -10.0,
            'key': 5,
            'mode': 1
        }
        
        title_lower = title.lower()
        artist_lower = artist.lower()
        
        # Genre-based adjustments
        if any(word in title_lower or word in artist_lower for word in ['rock', 'metal', 'punk']):
            features.update({
                'energy': 0.8,
                'loudness': -5.0,
                'tempo': 140.0,
                'acousticness': 0.1
            })
        elif any(word in title_lower or word in artist_lower for word in ['jazz', 'blues']):
            features.update({
                'acousticness': 0.7,
                'instrumentalness': 0.3,
                'tempo': 100.0
            })
        elif any(word in title_lower or word in artist_lower for word in ['dance', 'edm', 'electronic']):
            features.update({
                'danceability': 0.8,
                'energy': 0.9,
                'instrumentalness': 0.4,
                'tempo': 128.0
            })
        elif any(word in title_lower or word in artist_lower for word in ['acoustic', 'folk']):
            features.update({
                'acousticness': 0.9,
                'energy': 0.3,
                'loudness': -15.0,
                'tempo': 90.0
            })
        
        # Mood-based adjustments from title
        if any(word in title_lower for word in ['happy', 'joy', 'celebration', 'party']):
            features['valence'] = 0.8
            features['danceability'] = min(0.9, features['danceability'] + 0.2)
        elif any(word in title_lower for word in ['sad', 'melancholy', 'blue', 'lonely']):
            features['valence'] = 0.2
            features['energy'] = max(0.1, features['energy'] - 0.3)
        
        # Era-based adjustments (if we can guess from artist patterns)
        if any(word in artist_lower for word in ['beatles', 'stones', 'elvis', 'sinatra']):
            features['acousticness'] = min(0.8, features['acousticness'] + 0.3)
            
        return EnhancedAudioFeatures(
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
            source="estimation",
            confidence=0.4  # Lower confidence for estimation
        )
    
    def get_audio_features(self, title: str, artist: str) -> EnhancedAudioFeatures:
        """Get audio features using multi-tier approach"""
        self.stats["total_requests"] += 1
        
        # Tier 1: Historical dataset lookup
        features = self.lookup_historical_features(title, artist)
        if features:
            self.stats["historical_hits"] += 1
            return features
        
        # Tier 2: Essentia analysis (when implemented)
        features = self.analyze_with_essentia(title, artist)
        if features:
            self.stats["essentia_analysis"] += 1
            return features
        
        # Tier 3: Enhanced estimation
        self.stats["estimation_fallback"] += 1
        logger.info(f"Using enhanced estimation for: {title} by {artist}")
        return self.estimate_features(title, artist)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total = self.stats["total_requests"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "historical_hit_rate": self.stats["historical_hits"] / total,
            "essentia_rate": self.stats["essentia_analysis"] / total,
            "estimation_rate": self.stats["estimation_fallback"] / total
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Test the enhanced audio features system"""
    logging.basicConfig(level=logging.INFO)
    
    provider = EnhancedAudioFeaturesProvider()
    
    # Test cases
    test_songs = [
        ("Bohemian Rhapsody", "Queen"),
        ("Hotel California", "Eagles"),
        ("Imagine", "John Lennon"),
        ("Shape of You", "Ed Sheeran"),  # Might not be in historical data
        ("Some Modern Song", "Unknown Artist")  # Definitely not in data
    ]
    
    print("🎵 Enhanced Audio Features Test")
    print("=" * 50)
    
    for title, artist in test_songs:
        print(f"\n🎵 Testing: {title} by {artist}")
        features = provider.get_audio_features(title, artist)
        
        print(f"   Source: {features.source} (confidence: {features.confidence:.1f})")
        print(f"   Energy: {features.energy:.2f}, Danceability: {features.danceability:.2f}")
        print(f"   Valence: {features.valence:.2f}, Tempo: {features.tempo:.0f} BPM")
        if features.year:
            print(f"   Year: {features.year}")
    
    # Show statistics
    stats = provider.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Historical hits: {stats['historical_hits']} ({stats.get('historical_hit_rate', 0)*100:.1f}%)")
    print(f"   Estimation fallback: {stats['estimation_fallback']} ({stats.get('estimation_rate', 0)*100:.1f}%)")
    
    provider.close()

if __name__ == "__main__":
    main()
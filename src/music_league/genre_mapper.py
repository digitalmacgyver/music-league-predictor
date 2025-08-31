#!/usr/bin/env python3
"""
Genre Relationship Mapper

A sophisticated genre classification and relationship system that:
1. Fetches artist genres from Spotify API
2. Builds genre relationship graphs from co-occurrence data
3. Calculates genre distances for intelligent filtering
4. Caches all data for performance

Simple interface for scout:
    mapper = GenreMapper()
    is_match = mapper.matches_genre(artist_name, target_genre='rock', max_distance=0.3)
"""

import os
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class GenreMapper:
    """
    Maps genre relationships and calculates genre distances.
    
    Uses multiple data sources:
    - Spotify API for artist genres
    - Co-occurrence analysis from artist data
    - Manual genre hierarchy definitions
    - Cached data for performance
    """
    
    def __init__(self, cache_dir: str = "data/genre_cache", verbose: bool = False):
        """
        Initialize the genre mapper.
        
        Args:
            cache_dir: Directory for caching genre data
            verbose: Enable verbose logging
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # Initialize Spotify client
        self.spotify = self._init_spotify()
        
        # Common genre aliases
        self.genre_aliases = {
            'hip-hop': 'hip hop',
            'hip hop music': 'hip hop',
            'r and b': 'r&b',
            'rhythm and blues': 'r&b',
            'indie': 'indie rock',  # Default indie to indie rock
            'prog rock': 'progressive rock',
            'prog metal': 'progressive metal',
            'psych rock': 'psychedelic rock',
            'synth pop': 'synthpop',  # Normalize variations
            'synth-pop': 'synthpop',
            'post punk': 'post-punk',
            'pop-punk': 'pop punk',
            'antifolk': 'anti-folk',
            'dark wave': 'darkwave',
            'oldschool hip hop': 'old school hip hop',
            'traditional country': 'country',
            'alt country': 'alt-country',
            'alternative country': 'alt-country',
            'singer songwriter': 'singer-songwriter',
            'roots rock': 'folk rock',
            'irish folk': 'celtic',
            'irish rock': 'celtic rock',
        }
        
        # Load or initialize genre data
        self.artist_genres_cache = self._load_cache("artist_genres.json", {})
        self.genre_relationships = self._load_cache("genre_relationships.pkl", None)
        self.cooccurrence_matrix = self._load_cache("cooccurrence_matrix.pkl", {})
        
        # Initialize genre relationships if not cached
        if self.genre_relationships is None:
            self.genre_relationships = self._build_initial_relationships()
            self._save_cache("genre_relationships.pkl", self.genre_relationships)
        
        # Genre distance cache (calculated on demand)
        self.distance_cache = {}
        
        if self.verbose:
            logger.info(f"GenreMapper initialized with {len(self.artist_genres_cache)} cached artists")
    
    def _init_spotify(self) -> Optional[spotipy.Spotify]:
        """Initialize Spotify client if credentials are available."""
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if client_id and client_secret:
            try:
                auth = SpotifyClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret
                )
                return spotipy.Spotify(auth_manager=auth)
            except Exception as e:
                logger.warning(f"Failed to initialize Spotify client: {e}")
                return None
        return None
    
    def _load_cache(self, filename: str, default: Any) -> Any:
        """Load cached data from file."""
        cache_path = self.cache_dir / filename
        if cache_path.exists():
            try:
                if filename.endswith('.json'):
                    with open(cache_path, 'r') as f:
                        return json.load(f)
                elif filename.endswith('.pkl'):
                    with open(cache_path, 'rb') as f:
                        return pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache {filename}: {e}")
        return default
    
    def _save_cache(self, filename: str, data: Any) -> None:
        """Save data to cache file."""
        cache_path = self.cache_dir / filename
        try:
            if filename.endswith('.json'):
                with open(cache_path, 'w') as f:
                    json.dump(data, f, indent=2)
            elif filename.endswith('.pkl'):
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save cache {filename}: {e}")
    
    def _build_initial_relationships(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Build initial genre relationship hierarchy.
        This is a starting point that will be enhanced with real data.
        """
        relationships = {
            # Rock family
            'rock': {
                'subgenres': ['hard rock', 'soft rock', 'indie rock', 'alternative rock', 
                             'progressive rock', 'punk rock', 'classic rock', 'art rock',
                             'psychedelic rock', 'blues rock', 'folk rock', 'glam rock',
                             'yacht rock', 'gothic rock', 'post-rock', 'math rock'],
                'parent': None,
                'siblings': ['pop', 'blues', 'folk'],
                'near_neighbors': ['alternative', 'indie', 'grunge', 'punk'],
            },
            'hard rock': {
                'subgenres': ['heavy metal', 'glam metal', 'stoner rock'],
                'parent': 'rock',
                'siblings': ['blues rock', 'psychedelic rock'],
                'near_neighbors': ['metal', 'grunge', 'punk rock'],
            },
            'heavy metal': {
                'subgenres': ['thrash metal', 'death metal', 'black metal', 'power metal',
                             'doom metal', 'progressive metal', 'symphonic metal'],
                'parent': 'hard rock',
                'siblings': ['glam metal', 'stoner rock'],
                'near_neighbors': ['hard rock', 'industrial', 'metalcore', 'metal'],
            },
            'indie rock': {
                'subgenres': ['indie pop', 'lo-fi', 'math rock', 'post-rock'],
                'parent': 'rock',
                'siblings': ['alternative rock', 'art rock'],
                'near_neighbors': ['indie', 'alternative', 'indie folk'],
            },
            
            # Pop family
            'pop': {
                'subgenres': ['dance pop', 'electropop', 'indie pop', 'synth-pop',
                             'teen pop', 'art pop', 'chamber pop', 'dream pop',
                             'synthpop', 'pop punk', 'baroque pop'],
                'parent': None,
                'siblings': ['rock', 'r&b', 'dance'],
                'near_neighbors': ['indie', 'alternative', 'new wave'],
            },
            'indie pop': {
                'subgenres': ['bedroom pop', 'twee pop'],
                'parent': 'pop',
                'siblings': ['dream pop', 'chamber pop'],
                'near_neighbors': ['indie rock', 'indie folk', 'lo-fi'],
            },
            
            # Electronic family
            'electronic': {
                'subgenres': ['house', 'techno', 'trance', 'dubstep', 'drum and bass',
                             'ambient', 'idm', 'edm', 'synthwave', 'trip hop',
                             'darkwave', 'industrial'],
                'parent': None,
                'siblings': ['dance', 'experimental'],
                'near_neighbors': ['synth-pop', 'new wave', 'synthpop'],
            },
            
            # Hip-hop family
            'hip hop': {
                'subgenres': ['rap', 'trap', 'conscious hip hop', 'gangsta rap',
                             'alternative hip hop', 'east coast hip hop', 'west coast hip hop',
                             'old school hip hop'],
                'parent': None,
                'siblings': ['r&b', 'funk', 'soul'],
                'near_neighbors': ['trap', 'grime', 'neo soul'],
            },
            
            # Folk family
            'folk': {
                'subgenres': ['folk rock', 'indie folk', 'traditional folk', 'anti-folk',
                             'folk punk', 'celtic', 'celtic rock', 'bluegrass', 'newgrass'],
                'parent': None,
                'siblings': ['rock', 'country', 'blues'],
                'near_neighbors': ['singer-songwriter', 'americana', 'roots rock'],
            },
            
            # Punk family
            'punk': {
                'subgenres': ['punk rock', 'pop punk', 'folk punk', 'post-punk', 
                             'hardcore punk', 'ska punk'],
                'parent': None,
                'siblings': ['rock', 'alternative'],
                'near_neighbors': ['grunge', 'indie rock', 'garage rock'],
            },
            
            # Country family
            'country': {
                'subgenres': ['country rock', 'alt-country', 'americana', 'bluegrass',
                             'honky tonk', 'outlaw country'],
                'parent': None,
                'siblings': ['folk', 'rock', 'blues'],
                'near_neighbors': ['southern rock', 'roots rock', 'singer-songwriter'],
            },
            
            # Jazz family
            'jazz': {
                'subgenres': ['bebop', 'cool jazz', 'jazz fusion', 'smooth jazz',
                             'jazz blues', 'hard bop', 'free jazz', 'swing music'],
                'parent': None,
                'siblings': ['blues', 'soul', 'funk'],
                'near_neighbors': ['r&b', 'fusion', 'experimental'],
            },
            
            # Additional important genres
            'singer-songwriter': {
                'subgenres': [],
                'parent': 'folk',
                'siblings': ['indie folk', 'anti-folk'],
                'near_neighbors': ['folk rock', 'acoustic', 'americana'],
            },
            
            'yacht rock': {
                'subgenres': [],
                'parent': 'soft rock',
                'siblings': ['smooth jazz', 'adult contemporary'],
                'near_neighbors': ['soft rock', 'pop rock', 'blue-eyed soul'],
            },
            
            'post-grunge': {
                'subgenres': [],
                'parent': 'grunge',
                'siblings': ['alternative rock', 'nu metal'],
                'near_neighbors': ['grunge', 'hard rock', 'alternative metal'],
            },
            
            'new wave': {
                'subgenres': ['synthpop', 'post-punk', 'darkwave'],
                'parent': None,
                'siblings': ['punk', 'electronic'],
                'near_neighbors': ['synth-pop', 'alternative', 'gothic rock'],
            },
            
            'grunge': {
                'subgenres': ['post-grunge'],
                'parent': 'alternative rock',
                'siblings': ['indie rock', 'punk rock'],
                'near_neighbors': ['alternative rock', 'hard rock', 'punk'],
            },
            
            'celtic': {
                'subgenres': ['celtic rock', 'celtic punk'],
                'parent': 'folk',
                'siblings': ['traditional folk', 'irish folk'],
                'near_neighbors': ['folk', 'world music', 'bluegrass'],
            },
            
            'metal': {
                'subgenres': ['heavy metal', 'thrash metal', 'death metal', 'black metal'],
                'parent': 'hard rock',
                'siblings': ['heavy metal', 'hard rock'],
                'near_neighbors': ['heavy metal', 'thrash metal', 'metalcore'],
            },
            
            # Add more as needed...
        }
        
        return relationships
    
    def get_artist_genres(self, artist_name: str) -> List[str]:
        """
        Get genres for an artist from Spotify API with caching.
        
        Args:
            artist_name: Name of the artist
            
        Returns:
            List of genre tags for the artist
        """
        # Check cache first
        cache_key = artist_name.lower()
        if cache_key in self.artist_genres_cache:
            return self.artist_genres_cache[cache_key]
        
        # Fetch from Spotify if available
        if self.spotify:
            try:
                # Search for artist
                results = self.spotify.search(q=artist_name, type='artist', limit=5)
                artists = results.get('artists', {}).get('items', [])
                
                for artist in artists:
                    # Try to match artist name (case-insensitive)
                    if artist['name'].lower() == artist_name.lower():
                        genres = artist.get('genres', [])
                        # Cache the result
                        self.artist_genres_cache[cache_key] = genres
                        self._save_cache("artist_genres.json", self.artist_genres_cache)
                        return genres
                
                # If no exact match, use first result if close enough
                if artists:
                    genres = artists[0].get('genres', [])
                    self.artist_genres_cache[cache_key] = genres
                    self._save_cache("artist_genres.json", self.artist_genres_cache)
                    return genres
                    
            except Exception as e:
                logger.warning(f"Failed to fetch genres for {artist_name}: {e}")
        
        # Return empty list if no data available
        return []
    
    def build_cooccurrence_matrix(self, sample_size: int = 1000) -> None:
        """
        Build genre co-occurrence matrix from artist data.
        
        Args:
            sample_size: Number of artists to sample for analysis
        """
        if self.verbose:
            print(f"Building co-occurrence matrix from {sample_size} artists...")
        
        cooccurrence = defaultdict(lambda: defaultdict(int))
        genre_counts = Counter()
        
        # Use cached artist data
        for artist, genres in list(self.artist_genres_cache.items())[:sample_size]:
            for genre in genres:
                genre_counts[genre] += 1
                for other_genre in genres:
                    if genre != other_genre:
                        cooccurrence[genre][other_genre] += 1
        
        # Normalize co-occurrences to get probability scores
        self.cooccurrence_matrix = {}
        for genre1, others in cooccurrence.items():
            self.cooccurrence_matrix[genre1] = {}
            for genre2, count in others.items():
                # Normalize by the minimum count of the two genres
                min_count = min(genre_counts[genre1], genre_counts[genre2])
                if min_count > 0:
                    self.cooccurrence_matrix[genre1][genre2] = count / min_count
        
        self._save_cache("cooccurrence_matrix.pkl", self.cooccurrence_matrix)
        
        if self.verbose:
            print(f"Built co-occurrence matrix with {len(self.cooccurrence_matrix)} genres")
    
    def calculate_genre_distance(self, genre1: str, genre2: str) -> float:
        """
        Calculate distance between two genres (0.0 = identical, 1.0 = unrelated).
        
        Uses multiple signals:
        1. Direct relationships (parent/child/sibling)
        2. Co-occurrence frequency
        3. Shared keywords
        
        Args:
            genre1: First genre
            genre2: Second genre
            
        Returns:
            Distance score between 0.0 and 1.0
        """
        # Normalize genre names
        g1 = self.genre_aliases.get(genre1.lower(), genre1.lower())
        g2 = self.genre_aliases.get(genre2.lower(), genre2.lower())
        
        # Check cache
        cache_key = tuple(sorted([g1, g2]))
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]
        
        # Same genre
        if g1 == g2:
            distance = 0.0
        
        # Check direct relationships
        elif g1 in self.genre_relationships:
            rel = self.genre_relationships[g1]
            if g2 in rel.get('subgenres', []):
                distance = 0.15  # Parent to child
            elif g2 == rel.get('parent'):
                distance = 0.15  # Child to parent
            elif g2 in rel.get('siblings', []):
                distance = 0.3   # Siblings
            elif g2 in rel.get('near_neighbors', []):
                distance = 0.4   # Near neighbors
            else:
                distance = None  # Check other methods
        else:
            distance = None
        
        # Check co-occurrence if no direct relationship
        if distance is None:
            if g1 in self.cooccurrence_matrix and g2 in self.cooccurrence_matrix[g1]:
                # Convert co-occurrence to distance (high co-occurrence = low distance)
                cooccur_score = self.cooccurrence_matrix[g1][g2]
                distance = 1.0 - min(cooccur_score, 1.0)
            else:
                # Check for shared keywords as last resort
                g1_words = set(g1.split())
                g2_words = set(g2.split())
                if g1_words & g2_words:  # Shared words
                    distance = 0.5
                else:
                    distance = 0.9  # Unrelated genres
        
        # Cache and return
        self.distance_cache[cache_key] = distance
        return distance
    
    def matches_genre(self, artist_name: str, target_genre: str, 
                     max_distance: float = 0.5) -> bool:
        """
        Check if an artist matches a target genre within distance threshold.
        
        This is the main interface for scout.py
        
        Args:
            artist_name: Name of the artist
            target_genre: Target genre to match
            max_distance: Maximum allowed genre distance (0.0-1.0)
            
        Returns:
            True if artist matches genre within threshold
        """
        artist_genres = self.get_artist_genres(artist_name)
        
        if not artist_genres:
            # No genre data available - could default to True or False
            return False
        
        # Check distance to each of the artist's genres
        min_distance = min(
            self.calculate_genre_distance(target_genre, genre)
            for genre in artist_genres
        )
        
        return min_distance <= max_distance
    
    def get_genre_match_info(self, artist_name: str, target_genre: str) -> Dict[str, Any]:
        """
        Get detailed genre match information for debugging/explanation.
        
        Args:
            artist_name: Name of the artist
            target_genre: Target genre to match
            
        Returns:
            Dictionary with match details
        """
        artist_genres = self.get_artist_genres(artist_name)
        
        if not artist_genres:
            return {
                'artist': artist_name,
                'target_genre': target_genre,
                'artist_genres': [],
                'matches': [],
                'best_match': None,
                'min_distance': 1.0
            }
        
        # Calculate distance to each genre
        matches = []
        for genre in artist_genres:
            distance = self.calculate_genre_distance(target_genre, genre)
            matches.append({
                'genre': genre,
                'distance': distance,
                'relationship': self._describe_relationship(target_genre, genre)
            })
        
        # Sort by distance
        matches.sort(key=lambda x: x['distance'])
        
        return {
            'artist': artist_name,
            'target_genre': target_genre,
            'artist_genres': artist_genres,
            'matches': matches,
            'best_match': matches[0] if matches else None,
            'min_distance': matches[0]['distance'] if matches else 1.0
        }
    
    def _describe_relationship(self, genre1: str, genre2: str) -> str:
        """Get human-readable description of genre relationship."""
        g1 = self.genre_aliases.get(genre1.lower(), genre1.lower())
        g2 = self.genre_aliases.get(genre2.lower(), genre2.lower())
        
        if g1 == g2:
            return "identical"
        
        if g1 in self.genre_relationships:
            rel = self.genre_relationships[g1]
            if g2 in rel.get('subgenres', []):
                return f"parent of {g2}"
            elif g2 == rel.get('parent'):
                return f"subgenre of {g2}"
            elif g2 in rel.get('siblings', []):
                return f"sibling genre"
            elif g2 in rel.get('near_neighbors', []):
                return "near neighbor"
        
        if g1 in self.cooccurrence_matrix and g2 in self.cooccurrence_matrix[g1]:
            score = self.cooccurrence_matrix[g1][g2]
            if score > 0.5:
                return "frequently co-occurs"
            elif score > 0.2:
                return "sometimes co-occurs"
        
        return "unrelated"
    
    def get_related_genres(self, genre: str, max_distance: float = 0.5) -> List[Tuple[str, float]]:
        """
        Get all genres related to a target genre within distance threshold.
        
        Args:
            genre: Target genre
            max_distance: Maximum distance threshold
            
        Returns:
            List of (genre, distance) tuples sorted by distance
        """
        related = []
        
        # Check all known genres
        all_genres = set()
        for g, rels in self.genre_relationships.items():
            all_genres.add(g)
            all_genres.update(rels.get('subgenres', []))
            all_genres.update(rels.get('siblings', []))
            all_genres.update(rels.get('near_neighbors', []))
            if rels.get('parent'):
                all_genres.add(rels['parent'])
        
        # Add genres from co-occurrence matrix
        all_genres.update(self.cooccurrence_matrix.keys())
        
        # Calculate distances
        for other_genre in all_genres:
            if other_genre != genre:
                distance = self.calculate_genre_distance(genre, other_genre)
                if distance <= max_distance:
                    related.append((other_genre, distance))
        
        # Sort by distance
        related.sort(key=lambda x: x[1])
        return related


# Simple interface functions for scout.py
def check_genre_match(artist: str, target_genre: str, max_distance: float = 0.5) -> bool:
    """
    Simple interface for checking if an artist matches a genre.
    
    Args:
        artist: Artist name
        target_genre: Target genre
        max_distance: Maximum genre distance (0.0-1.0)
        
    Returns:
        True if artist matches genre within threshold
    """
    mapper = GenreMapper()
    return mapper.matches_genre(artist, target_genre, max_distance)


def get_artist_genres(artist: str) -> List[str]:
    """
    Get genres for an artist.
    
    Args:
        artist: Artist name
        
    Returns:
        List of genre tags
    """
    mapper = GenreMapper()
    return mapper.get_artist_genres(artist)
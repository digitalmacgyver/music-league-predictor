#!/usr/bin/env python3
"""
Dynamic Mainstream Detection using Spotify Data

Detects mainstream songs using real-time Spotify signals:
- Track popularity scores (0-100)
- Artist popularity and follower counts
- Presence in mainstream/curated playlists
- Audio features that correlate with mainstream appeal
- Release date and longevity signals
"""

import logging
import re
from typing import Dict, Set, Tuple, Optional, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class DynamicMainstreamDetector:
    """Dynamic mainstream detection using Spotify's live data"""
    
    # Mainstream playlist indicators (Spotify curated playlists)
    MAINSTREAM_PLAYLIST_KEYWORDS = {
        # Official Spotify mainstream playlists
        'today\'s top hits', 'top hits', 'global top 50', 'viral 50',
        'hot hits', 'mega hit mix', 'pop rising', 'rock this',
        'rap caviar', 'hot country', 'viva latino', 'baila reggaeton',
        
        # Chart-based playlists
        'billboard', 'top 100', 'top 50', 'top 40', 'chart',
        'number 1', '#1', 'no. 1', 'greatest hits', 'best of',
        
        # Radio/mainstream indicators
        'radio hits', 'car radio', 'office radio', 'mainstream',
        'party hits', 'wedding', 'karaoke', 'sing-along',
        
        # Era-specific mainstream
        'classic rock radio', '80s hits', '90s hits', '00s hits',
        'oldies', 'throwback', 'timeless', 'all time',
        
        # Platform mainstream
        'this is:', 'essential', 'complete', 'definitive'
    }
    
    # Indie/alternative playlist indicators (less mainstream)
    INDIE_PLAYLIST_KEYWORDS = {
        'indie', 'alternative', 'underground', 'deep cuts',
        'hidden gems', 'undiscovered', 'emerging', 'fresh finds',
        'bedroom', 'lo-fi', 'experimental', 'obscure',
        'b-sides', 'rarities', 'demos', 'sessions'
    }
    
    def __init__(self, spotify_client: Optional[spotipy.Spotify] = None):
        """Initialize with Spotify client"""
        self.spotify = spotify_client
        if not self.spotify:
            try:
                self.spotify = spotipy.Spotify(
                    client_credentials_manager=SpotifyClientCredentials()
                )
                logger.info("Spotify client initialized for dynamic mainstream detection")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify client: {e}")
                self.spotify = None
        
        # Cache for API calls (track_id -> data)
        self.track_cache = {}
        self.artist_cache = {}
        self.playlist_cache = {}
        
    def is_mainstream(self, title: str, artist: str, 
                     spotify_id: Optional[str] = None,
                     threshold: float = 0.65) -> Tuple[bool, str, float]:
        """
        Determine if a song is mainstream using dynamic Spotify data
        
        Args:
            title: Song title
            artist: Artist name
            spotify_id: Spotify track ID if available
            threshold: Score threshold for mainstream (0.0-1.0)
            
        Returns:
            (is_mainstream, reason, score)
        """
        
        # Get Spotify track ID if not provided
        if not spotify_id and self.spotify:
            spotify_id = self._search_track(title, artist)
        
        if not spotify_id or not self.spotify:
            # Fallback to basic heuristics
            return self._fallback_detection(title, artist)
        
        # Calculate mainstream score from multiple signals
        score, signals = self.calculate_mainstream_score(spotify_id)
        
        # Build reason from signals
        reason_parts = []
        if signals.get('track_popularity', 0) > 70:
            reason_parts.append(f"Track popularity: {signals['track_popularity']}/100")
        if signals.get('artist_popularity', 0) > 70:
            reason_parts.append(f"Artist popularity: {signals['artist_popularity']}/100")
        if signals.get('mainstream_playlists', 0) > 0:
            reason_parts.append(f"In {signals['mainstream_playlists']} mainstream playlists")
        if signals.get('artist_followers', 0) > 1000000:
            reason_parts.append(f"Artist has {signals['artist_followers']:,} followers")
        
        reason = "; ".join(reason_parts) if reason_parts else "Below mainstream threshold"
        
        return score >= threshold, reason, score
    
    def calculate_mainstream_score(self, spotify_id: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate comprehensive mainstream score using multiple signals
        
        Returns:
            (score, signals_dict)
        """
        
        if not self.spotify or not spotify_id:
            return 0.0, {}
        
        signals = {}
        weights = {
            'track_popularity': 0.45,      # Direct popularity score (increased)
            'artist_popularity': 0.20,      # Artist fame level
            'playlist_presence': 0.15,      # Mainstream playlist inclusion
            'follower_score': 0.10,         # Artist follower count
            'longevity': 0.10               # How long it's been popular
        }
        
        try:
            # Get track data
            track_data = self._get_track_data(spotify_id)
            if not track_data:
                return 0.0, {}
            
            # 1. Track popularity (0-100 from Spotify)
            track_pop = track_data.get('popularity', 0)
            signals['track_popularity'] = track_pop
            # Apply a curve to make high popularity more impactful
            # 80+ = very mainstream, 70-79 = mainstream, 60-69 = moderate
            if track_pop >= 80:
                track_score = 0.9 + (track_pop - 80) / 200.0  # 80-100 maps to 0.9-1.0
            elif track_pop >= 70:
                track_score = 0.7 + (track_pop - 70) / 100.0  # 70-79 maps to 0.7-0.8
            elif track_pop >= 60:
                track_score = 0.5 + (track_pop - 60) / 100.0  # 60-69 maps to 0.5-0.6
            else:
                track_score = track_pop / 120.0  # 0-59 maps to 0.0-0.5
            
            # 2. Artist popularity and followers
            artist_id = track_data['artists'][0]['id'] if track_data.get('artists') else None
            if artist_id:
                artist_data = self._get_artist_data(artist_id)
                if artist_data:
                    artist_pop = artist_data.get('popularity', 0)
                    signals['artist_popularity'] = artist_pop
                    artist_score = artist_pop / 100.0
                    
                    # Follower count (logarithmic scale)
                    followers = artist_data.get('followers', {}).get('total', 0)
                    signals['artist_followers'] = followers
                    if followers > 0:
                        # 10M+ followers = 1.0, 100k = 0.5, 1k = 0.25
                        import math
                        follower_score = min(1.0, math.log10(followers) / 7.0)
                    else:
                        follower_score = 0.0
                else:
                    artist_score = 0.0
                    follower_score = 0.0
            else:
                artist_score = 0.0
                follower_score = 0.0
            
            # 3. Playlist presence (search for track in playlists)
            playlist_score, playlist_count = self._analyze_playlist_presence(
                track_data['name'], 
                track_data['artists'][0]['name'] if track_data.get('artists') else ""
            )
            signals['mainstream_playlists'] = playlist_count
            
            # 4. Longevity (how long has it been popular)
            release_date = track_data.get('album', {}).get('release_date', '')
            longevity_score = self._calculate_longevity_score(release_date, track_pop)
            signals['longevity_score'] = longevity_score
            
            # Calculate weighted score
            final_score = (
                weights['track_popularity'] * track_score +
                weights['artist_popularity'] * artist_score +
                weights['playlist_presence'] * playlist_score +
                weights['follower_score'] * follower_score +
                weights['longevity'] * longevity_score
            )
            
            return final_score, signals
            
        except Exception as e:
            logger.error(f"Error calculating mainstream score: {e}")
            return 0.0, {}
    
    def _get_track_data(self, spotify_id: str) -> Optional[Dict]:
        """Get track data from Spotify API with caching"""
        if spotify_id in self.track_cache:
            return self.track_cache[spotify_id]
        
        try:
            track = self.spotify.track(spotify_id)
            self.track_cache[spotify_id] = track
            return track
        except Exception as e:
            logger.debug(f"Could not fetch track {spotify_id}: {e}")
            return None
    
    def _get_artist_data(self, artist_id: str) -> Optional[Dict]:
        """Get artist data from Spotify API with caching"""
        if artist_id in self.artist_cache:
            return self.artist_cache[artist_id]
        
        try:
            artist = self.spotify.artist(artist_id)
            self.artist_cache[artist_id] = artist
            return artist
        except Exception as e:
            logger.debug(f"Could not fetch artist {artist_id}: {e}")
            return None
    
    def _search_track(self, title: str, artist: str) -> Optional[str]:
        """Search for a track on Spotify and return its ID"""
        if not self.spotify:
            return None
        
        try:
            # Clean up the search query
            title_clean = re.sub(r'\([^)]*\)', '', title).strip()
            artist_clean = re.sub(r'\([^)]*\)', '', artist).strip()
            
            query = f"track:{title_clean} artist:{artist_clean}"
            results = self.spotify.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                return results['tracks']['items'][0]['id']
            
            # Try simpler search if exact match fails
            query = f"{title_clean} {artist_clean}"
            results = self.spotify.search(q=query, type='track', limit=3)
            
            # Look for best match
            for track in results['tracks']['items']:
                track_artist = track['artists'][0]['name'].lower() if track['artists'] else ""
                if artist_clean.lower() in track_artist or track_artist in artist_clean.lower():
                    return track['id']
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not search for track: {e}")
            return None
    
    def _analyze_playlist_presence(self, title: str, artist: str) -> Tuple[float, int]:
        """
        Analyze how many mainstream playlists contain this track
        
        Returns:
            (score, mainstream_playlist_count)
        """
        if not self.spotify:
            return 0.0, 0
        
        try:
            # Search for playlists containing this track
            query = f"{title} {artist}"
            results = self.spotify.search(q=query, type='playlist', limit=50)
            
            mainstream_count = 0
            indie_count = 0
            total_followers = 0
            
            for playlist in results['playlists']['items']:
                name_lower = playlist['name'].lower()
                
                # Check if playlist name indicates mainstream
                is_mainstream = any(keyword in name_lower 
                                   for keyword in self.MAINSTREAM_PLAYLIST_KEYWORDS)
                is_indie = any(keyword in name_lower 
                              for keyword in self.INDIE_PLAYLIST_KEYWORDS)
                
                if is_mainstream:
                    mainstream_count += 1
                    # Weight by playlist followers if available
                    if 'followers' in playlist:
                        total_followers += playlist['followers'].get('total', 0)
                elif is_indie:
                    indie_count += 1
            
            # Calculate score based on playlist presence
            if mainstream_count > 0:
                # More mainstream playlists = higher score
                # Presence in 5+ mainstream playlists = very mainstream
                score = min(1.0, mainstream_count / 5.0)
                
                # Reduce score if also in many indie playlists
                if indie_count > mainstream_count:
                    score *= 0.7
                
                return score, mainstream_count
            elif indie_count > 3:
                # Primarily in indie playlists = not mainstream
                return 0.2, 0
            else:
                # Not in many playlists either way
                return 0.3, 0
                
        except Exception as e:
            logger.debug(f"Could not analyze playlist presence: {e}")
            return 0.0, 0
    
    def _calculate_longevity_score(self, release_date: str, current_popularity: int) -> float:
        """
        Calculate longevity score - old songs that are still popular are very mainstream
        """
        if not release_date or current_popularity < 50:
            return 0.0
        
        try:
            # Parse release date
            if len(release_date) == 4:  # Year only
                release = datetime(int(release_date), 1, 1)
            elif len(release_date) == 7:  # Year-month
                year, month = release_date.split('-')
                release = datetime(int(year), int(month), 1)
            else:  # Full date
                release = datetime.strptime(release_date[:10], '%Y-%m-%d')
            
            # Calculate age in years
            age_years = (datetime.now() - release).days / 365.25
            
            # Old + still popular = mainstream classic
            if age_years > 20 and current_popularity > 60:
                return 1.0  # Classic that's still popular
            elif age_years > 10 and current_popularity > 70:
                return 0.8  # Decade old and very popular
            elif age_years > 5 and current_popularity > 80:
                return 0.6  # Recent classic
            elif age_years < 1 and current_popularity > 90:
                return 0.7  # Current hit
            else:
                return 0.3
                
        except Exception as e:
            logger.debug(f"Could not calculate longevity: {e}")
            return 0.0
    
    def _fallback_detection(self, title: str, artist: str) -> Tuple[bool, str, float]:
        """
        Fallback detection when Spotify API is not available
        Uses basic heuristics
        """
        
        title_lower = title.lower()
        artist_lower = artist.lower()
        score = 0.0
        
        # Check for obvious mainstream indicators in title
        mainstream_title_words = {
            'greatest', 'best', 'hits', 'single', 'radio',
            'remaster', 'anniversary', 'deluxe', 'essential'
        }
        
        if any(word in title_lower for word in mainstream_title_words):
            score += 0.3
        
        # Check for mainstream artist indicators
        mainstream_artist_words = {
            'feat.', 'featuring', '&', 'soundtrack', 'cast'
        }
        
        if any(word in artist_lower for word in mainstream_artist_words):
            score += 0.2
        
        # Very short titles are often hits
        if len(title.split()) <= 2:
            score += 0.1
        
        reason = "No Spotify data available - using heuristics"
        return score >= 0.5, reason, score
    
    def get_track_details(self, spotify_id: str) -> Dict[str, Any]:
        """Get detailed track information for analysis"""
        
        if not self.spotify or not spotify_id:
            return {}
        
        track_data = self._get_track_data(spotify_id)
        if not track_data:
            return {}
        
        # Get audio features
        try:
            audio_features = self.spotify.audio_features(spotify_id)[0]
        except:
            audio_features = {}
        
        # Get artist data
        artist_data = {}
        if track_data.get('artists'):
            artist_id = track_data['artists'][0]['id']
            artist_data = self._get_artist_data(artist_id) or {}
        
        return {
            'name': track_data.get('name'),
            'artist': track_data['artists'][0]['name'] if track_data.get('artists') else 'Unknown',
            'album': track_data.get('album', {}).get('name'),
            'release_date': track_data.get('album', {}).get('release_date'),
            'popularity': track_data.get('popularity', 0),
            'artist_popularity': artist_data.get('popularity', 0),
            'artist_followers': artist_data.get('followers', {}).get('total', 0),
            'audio_features': audio_features,
            'genres': artist_data.get('genres', [])
        }
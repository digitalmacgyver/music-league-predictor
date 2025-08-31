#!/usr/bin/env python3
"""
Release Date Verification Module

Provides multiple strategies to verify song release dates:
1. Wikipedia lookups for notable songs
2. Spotify album metadata (with compilation filtering)
3. Cached results for performance
"""

import re
import requests
from typing import Optional, Dict, Any, Tuple
import logging
from urllib.parse import quote
import spotipy
from datetime import datetime
import json
import os
from music_league.config import BASE_DIR

logger = logging.getLogger(__name__)

class ReleaseDateVerifier:
    """Verifies song release dates using multiple sources"""
    
    def __init__(self, spotify_client: Optional[spotipy.Spotify] = None):
        self.spotify = spotify_client
        self.cache_file = os.path.join(BASE_DIR, "data", "release_date_cache.json")
        self.cache = self._load_cache()
        
        # Common compilation/remaster keywords that indicate non-original releases
        self.compilation_keywords = [
            'compilation', 'greatest hits', 'best of', 'anthology', 'collection',
            'remaster', 'remastered', 'deluxe', 'expanded', 'live', 'acoustic',
            'demo', 'unreleased', 'b-sides', 'rarities', 'singles', 'hits'
        ]
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cached release date results"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load release date cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cached release date results"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save release date cache: {e}")
    
    def _cache_key(self, title: str, artist: str) -> str:
        """Create a cache key for a song"""
        return f"{title.lower()}|{artist.lower()}"
    
    def verify_song_era(self, title: str, artist: str, target_era: str) -> Tuple[bool, Optional[int], str]:
        """
        Verify if a song was first released in the target era
        
        Returns:
            (is_from_era, release_year, source)
        """
        cache_key = self._cache_key(title, artist)
        
        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            release_year = cached.get('release_year')
            source = cached.get('source', 'cache')
            is_from_era = self._is_year_in_era(release_year, target_era) if release_year else False
            return is_from_era, release_year, source
        
        # Try Wikipedia first for notable songs
        release_year, source = self._get_wikipedia_release_date(title, artist)
        
        # Fallback to Spotify if Wikipedia fails
        if not release_year and self.spotify:
            release_year, source = self._get_spotify_release_date(title, artist)
        
        # Cache the result
        self.cache[cache_key] = {
            'release_year': release_year,
            'source': source,
            'last_checked': datetime.now().isoformat()
        }
        self._save_cache()
        
        is_from_era = self._is_year_in_era(release_year, target_era) if release_year else False
        return is_from_era, release_year, source
    
    def _is_year_in_era(self, year: int, era: str) -> bool:
        """Check if a year falls within the specified era"""
        era_ranges = {
            '60s': (1960, 1969),
            '70s': (1970, 1979), 
            '80s': (1980, 1989),
            '90s': (1990, 1999),
            '00s': (2000, 2009),
            '10s': (2010, 2019),
            '20s': (2020, 2029)
        }
        
        if era not in era_ranges:
            return False
        
        start, end = era_ranges[era]
        return start <= year <= end
    
    def _get_wikipedia_release_date(self, title: str, artist: str) -> Tuple[Optional[int], str]:
        """Get release date from Wikipedia"""
        try:
            # Search for the song on Wikipedia
            search_query = f'"{title}" {artist} wikipedia'
            search_url = f"https://en.wikipedia.org/w/api.php"
            
            # First, search for the page
            search_params = {
                'action': 'query',
                'list': 'search',
                'srsearch': f'"{title}" {artist}',
                'format': 'json',
                'srlimit': 3
            }
            
            response = requests.get(search_url, params=search_params, timeout=10)
            response.raise_for_status()
            search_data = response.json()
            
            if not search_data.get('query', {}).get('search'):
                return None, 'wikipedia_not_found'
            
            # Try the top search results
            for result in search_data['query']['search'][:2]:
                page_title = result['title']
                
                # Get the page content
                content_params = {
                    'action': 'query',
                    'titles': page_title,
                    'prop': 'extracts',
                    'exintro': True,
                    'explaintext': True,
                    'format': 'json'
                }
                
                content_response = requests.get(search_url, params=content_params, timeout=10)
                content_response.raise_for_status()
                content_data = content_response.json()
                
                pages = content_data.get('query', {}).get('pages', {})
                for page_id, page_data in pages.items():
                    extract = page_data.get('extract', '')
                    
                    # Look for release date patterns
                    release_year = self._extract_release_year_from_text(extract)
                    if release_year:
                        logger.info(f"Found Wikipedia release date for '{title}' by {artist}: {release_year}")
                        return release_year, 'wikipedia'
            
            return None, 'wikipedia_no_date'
            
        except Exception as e:
            logger.warning(f"Wikipedia lookup failed for '{title}' by {artist}: {e}")
            return None, 'wikipedia_error'
    
    def _extract_release_year_from_text(self, text: str) -> Optional[int]:
        """Extract release year from Wikipedia text"""
        # Look for common release date patterns
        patterns = [
            r'released.*?in.*?(\d{4})',
            r'(\d{4}).*?single',
            r'written.*?in.*?(\d{4})',
            r'recorded.*?in.*?(\d{4})',
            r'first released.*?(\d{4})',
            r'originally.*?(\d{4})',
            r'".*?".*?is.*?(\d{4})',
            r'(\d{4}).*?song',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                year = int(match)
                # Reasonable range for popular music
                if 1950 <= year <= 2024:
                    return year
        
        return None
    
    def _get_spotify_release_date(self, title: str, artist: str) -> Tuple[Optional[int], str]:
        """Get release date from Spotify album metadata"""
        try:
            # Search for the track on Spotify
            query = f'track:"{title}" artist:"{artist}"'
            results = self.spotify.search(q=query, type='track', limit=10)
            
            tracks = results.get('tracks', {}).get('items', [])
            if not tracks:
                # Try broader search
                query = f'{title} {artist}'
                results = self.spotify.search(q=query, type='track', limit=10)
                tracks = results.get('tracks', {}).get('items', [])
            
            if not tracks:
                return None, 'spotify_not_found'
            
            # Find the best matching track and get its earliest album release
            earliest_year = None
            best_match = None
            
            for track in tracks:
                # Check if this is a good match
                track_title = track['name'].lower()
                track_artists = [a['name'].lower() for a in track['artists']]
                
                if (title.lower() in track_title or track_title in title.lower()) and \
                   any(artist.lower() in ta or ta in artist.lower() for ta in track_artists):
                    
                    album = track.get('album', {})
                    album_name = album.get('name', '').lower()
                    release_date = album.get('release_date', '')
                    
                    # Skip compilations and live albums
                    if any(keyword in album_name for keyword in self.compilation_keywords):
                        continue
                    
                    # Extract year from release date
                    if release_date:
                        year = int(release_date[:4])
                        if not earliest_year or year < earliest_year:
                            earliest_year = year
                            best_match = f"{album_name} ({year})"
            
            if earliest_year:
                logger.info(f"Found Spotify release date for '{title}' by {artist}: {earliest_year} (from {best_match})")
                return earliest_year, 'spotify'
            
            return None, 'spotify_no_date'
            
        except Exception as e:
            logger.warning(f"Spotify lookup failed for '{title}' by {artist}: {e}")
            return None, 'spotify_error'
    
    def bulk_verify_era(self, songs: list, target_era: str) -> list:
        """Verify era for multiple songs and return only those from the target era"""
        verified_songs = []
        
        for song in songs:
            title = song.get('title', '')
            artist = song.get('artist', '')
            
            if not title or not artist:
                continue
            
            is_from_era, release_year, source = self.verify_song_era(title, artist, target_era)
            
            if is_from_era:
                song_copy = song.copy()
                song_copy['verified_release_year'] = release_year
                song_copy['verification_source'] = source
                verified_songs.append(song_copy)
                logger.info(f"✅ Era verified: '{title}' by {artist} ({release_year}, {source})")
            else:
                logger.info(f"❌ Era mismatch: '{title}' by {artist} ({release_year or 'unknown'}, {source})")
        
        return verified_songs
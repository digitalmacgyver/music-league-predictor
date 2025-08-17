#!/usr/bin/env python3
"""
Spotify utilities for handling track IDs and URLs
"""

import re
from typing import Optional, Set, List, Dict, Any
import spotipy
import logging

logger = logging.getLogger(__name__)

class SpotifyUtils:
    """Utilities for working with Spotify track IDs and URLs"""
    
    @staticmethod
    def extract_track_id(spotify_url: str) -> Optional[str]:
        """Extract Spotify track ID from URL"""
        if not spotify_url:
            return None
        
        # Handle different Spotify URL formats
        patterns = [
            r'spotify:track:([a-zA-Z0-9]+)',
            r'open\.spotify\.com/track/([a-zA-Z0-9]+)',
            r'/track/([a-zA-Z0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, spotify_url)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def build_spotify_url(track_id: str) -> str:
        """Build Spotify URL from track ID"""
        return f"https://open.spotify.com/track/{track_id}"
    
    @staticmethod
    def get_existing_spotify_ids(conn) -> Set[str]:
        """Get all existing Spotify track IDs from the database"""
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT spotify_url FROM songs WHERE spotify_url IS NOT NULL")
        
        existing_ids = set()
        for row in cursor.fetchall():
            spotify_url = row['spotify_url']
            track_id = SpotifyUtils.extract_track_id(spotify_url)
            if track_id:
                existing_ids.add(track_id)
        
        logger.info(f"Loaded {len(existing_ids)} existing Spotify track IDs from database")
        return existing_ids
    
    @staticmethod
    def get_spotify_track_id(spotify_client: spotipy.Spotify, title: str, artist: str) -> Optional[str]:
        """Get Spotify track ID for a song"""
        try:
            # Try exact search first
            query = f'track:"{title}" artist:"{artist}"'
            results = spotify_client.search(q=query, type='track', limit=5)
            
            tracks = results.get('tracks', {}).get('items', [])
            
            # Look for exact or close match
            for track in tracks:
                track_title = track['name'].lower()
                track_artists = [a['name'].lower() for a in track['artists']]
                
                # Check for exact or very close match
                if (title.lower() in track_title or track_title in title.lower()) and \
                   any(artist.lower() in ta or ta in artist.lower() for ta in track_artists):
                    return track['id']
            
            # Try broader search if exact search fails
            if not tracks:
                query = f'{title} {artist}'
                results = spotify_client.search(q=query, type='track', limit=10)
                tracks = results.get('tracks', {}).get('items', [])
                
                for track in tracks:
                    track_title = track['name'].lower()
                    track_artists = [a['name'].lower() for a in track['artists']]
                    
                    if (title.lower() in track_title or track_title in title.lower()) and \
                       any(artist.lower() in ta or ta in artist.lower() for ta in track_artists):
                        return track['id']
            
            return None
            
        except Exception as e:
            logger.warning(f"Spotify search failed for '{title}' by {artist}: {e}")
            return None
    
    @staticmethod
    def enrich_candidates_with_spotify_ids(candidates: List[Dict[str, Any]], 
                                         spotify_client: spotipy.Spotify) -> List[Dict[str, Any]]:
        """Add Spotify track IDs to candidate songs"""
        enriched_candidates = []
        
        for candidate in candidates:
            title = candidate.get('title', '')
            artist = candidate.get('artist', '')
            
            if not title or not artist:
                continue
            
            # Get Spotify track ID
            track_id = SpotifyUtils.get_spotify_track_id(spotify_client, title, artist)
            
            if track_id:
                enriched_candidate = candidate.copy()
                enriched_candidate['spotify_track_id'] = track_id
                enriched_candidate['spotify_url'] = SpotifyUtils.build_spotify_url(track_id)
                enriched_candidates.append(enriched_candidate)
                logger.debug(f"✅ Found Spotify ID for '{title}' by {artist}: {track_id}")
            else:
                logger.warning(f"❌ No Spotify ID found for '{title}' by {artist}")
        
        logger.info(f"Enriched {len(enriched_candidates)}/{len(candidates)} candidates with Spotify IDs")
        return enriched_candidates
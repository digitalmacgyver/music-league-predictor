#!/usr/bin/env ./venv/bin/python3
"""
Spotify Playlist-Based Song Discovery System

Discovers candidate songs by searching public Spotify playlists whose titles 
match the theme, then extracts and analyzes their tracks.
"""

import os
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class PlaylistMatch:
    """A playlist that matches our search theme"""
    id: str
    name: str
    owner: str
    track_count: int
    public: bool
    relevance_score: float
    description: Optional[str] = None

@dataclass
class PlaylistTrack:
    """A track extracted from a playlist"""
    title: str
    artist: str
    album: Optional[str] = None
    spotify_id: Optional[str] = None
    popularity: Optional[int] = None
    source_playlist: Optional[str] = None

class SpotifyPlaylistDiscovery:
    """Discover songs through thematically relevant Spotify playlists"""
    
    def __init__(self):
        self.spotify = None
        self.stats = {
            "playlists_searched": 0,
            "playlists_found": 0,
            "tracks_extracted": 0,
            "unique_tracks": 0
        }
        
        # Initialize Spotify client
        if os.getenv('SPOTIFY_CLIENT_ID') and os.getenv('SPOTIFY_CLIENT_SECRET'):
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                logger.info("Spotify playlist discovery initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify client: {e}")
        else:
            logger.warning("Spotify credentials not found - playlist discovery unavailable")
    
    def calculate_playlist_relevance(self, playlist_name: str, theme: str, description: str = "",
                                   exclude_mainstream: bool = False, era: str = None, genre: str = None) -> float:
        """Calculate how relevant a playlist is to our theme"""
        
        theme_lower = theme.lower()
        playlist_lower = playlist_name.lower()
        desc_lower = description.lower() if description else ""
        
        score = 0.0
        
        # Exact theme match in title
        if theme_lower in playlist_lower:
            score += 0.8
        
        # Theme words in title
        theme_words = set(re.findall(r'\b\w+\b', theme_lower))
        playlist_words = set(re.findall(r'\b\w+\b', playlist_lower))
        word_overlap = len(theme_words.intersection(playlist_words))
        
        if word_overlap > 0:
            score += min(0.6, word_overlap * 0.2)
        
        # Theme words in description
        if desc_lower:
            desc_words = set(re.findall(r'\b\w+\b', desc_lower))
            desc_overlap = len(theme_words.intersection(desc_words))
            if desc_overlap > 0:
                score += min(0.3, desc_overlap * 0.1)
        
        # Handle mainstream exclusion
        if exclude_mainstream:
            # Heavy penalty for mainstream indicators
            mainstream_terms = ['hits', 'top 100', 'top 50', 'best of', 'greatest', 'billboard', 
                              'chart', 'popular', 'mainstream', 'radio', 'commercial', 'smash hits']
            mainstream_count = sum(1 for term in mainstream_terms if term in playlist_lower)
            if mainstream_count > 0:
                score -= 0.8  # Heavy penalty for mainstream playlists
            
            # Bonus for underground/alternative indicators
            underground_terms = ['underground', 'indie', 'alternative', 'hidden gems', 'deep cuts',
                               'obscure', 'rare', 'b-sides', 'undiscovered', 'cult', 'niche']
            if any(term in playlist_lower for term in underground_terms):
                score += 0.3
        else:
            # Normal mode: bonus for quality indicators
            quality_indicators = ['curated', 'best', 'ultimate', 'essential', 'top']
            if any(indicator in playlist_lower for indicator in quality_indicators):
                score += 0.1
        
        # Era-specific filtering
        if era:
            # Bonus for era matches
            era_terms = {
                '60s': ['60s', 'sixties', '1960'],
                '70s': ['70s', 'seventies', '1970'],
                '80s': ['80s', 'eighties', '1980'],
                '90s': ['90s', 'nineties', '1990'],
                '00s': ['00s', '2000s', 'noughties'],
                '10s': ['10s', '2010s'],
                '20s': ['20s', '2020s']
            }
            
            if era in era_terms:
                for term in era_terms[era]:
                    if term in playlist_lower:
                        score += 0.4
                        break
                        
                # Penalty for other eras
                for other_era, terms in era_terms.items():
                    if other_era != era:
                        for term in terms:
                            if term in playlist_lower:
                                score -= 0.3
                                break
        
        # Genre-specific filtering
        if genre:
            # Bonus for genre matches
            genre_lower = genre.lower()
            if genre_lower in playlist_lower:
                score += 0.4
            
            # Genre synonyms
            genre_synonyms = {
                'rock': ['rock', 'alternative', 'indie rock', 'classic rock'],
                'pop': ['pop', 'top 40', 'mainstream'],
                'hip-hop': ['hip hop', 'hip-hop', 'rap', 'urban'],
                'electronic': ['electronic', 'edm', 'dance', 'techno', 'house'],
                'country': ['country', 'folk', 'americana', 'bluegrass'],
                'jazz': ['jazz', 'blues', 'swing', 'bebop'],
                'classical': ['classical', 'orchestral', 'symphony', 'baroque']
            }
            
            if genre in genre_synonyms:
                for synonym in genre_synonyms[genre]:
                    if synonym in playlist_lower:
                        score += 0.3
                        break
        
        # Penalty for very generic playlists
        generic_terms = ['mix', '2024', '2025', 'music', 'songs']
        generic_count = sum(1 for term in generic_terms if term in playlist_lower)
        if generic_count >= 3:
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def search_playlists_for_theme(self, theme: str, max_playlists: int = 20, 
                                 exclude_mainstream: bool = False, era: str = None, 
                                 genre: str = None) -> List[PlaylistMatch]:
        """Search for playlists that match the given theme"""
        
        if not self.spotify:
            logger.warning("Spotify client not available")
            return []
        
        self.stats["playlists_searched"] += 1
        
        try:
            logger.info(f"🔍 Searching playlists for theme: '{theme}'")
            
            # Search for playlists (ensure limit is at least 1)
            search_limit = max(1, min(50, max_playlists))
            results = self.spotify.search(q=theme, type='playlist', limit=search_limit)
            playlists = results['playlists']['items']
            
            logger.info(f"   Found {len(playlists)} potential playlists")
            
            # Score and filter playlists
            playlist_matches = []
            
            for playlist in playlists:
                if not playlist or not playlist.get('name'):
                    continue
                
                # Get playlist details
                name = playlist['name']
                owner_info = playlist.get('owner', {})
                owner = owner_info.get('display_name') or owner_info.get('id', 'Unknown')
                track_count = playlist.get('tracks', {}).get('total', 0)
                public = playlist.get('public', False)
                description = playlist.get('description', '')
                
                # Skip playlists with no tracks or private playlists
                if track_count == 0 or not public:
                    continue
                
                # Calculate relevance score
                relevance = self.calculate_playlist_relevance(name, theme, description, 
                                                            exclude_mainstream, era, genre)
                
                # Only include playlists with reasonable relevance
                if relevance >= 0.3:
                    playlist_matches.append(PlaylistMatch(
                        id=playlist['id'],
                        name=name,
                        owner=owner,
                        track_count=track_count,
                        public=public,
                        relevance_score=relevance,
                        description=description
                    ))
            
            # Sort by relevance score
            playlist_matches.sort(key=lambda x: x.relevance_score, reverse=True)
            
            self.stats["playlists_found"] += len(playlist_matches)
            
            logger.info(f"   ✅ Found {len(playlist_matches)} relevant playlists")
            for match in playlist_matches[:5]:  # Log top 5
                logger.info(f"      '{match.name}' by {match.owner} (score: {match.relevance_score:.2f}, {match.track_count} tracks)")
            
            return playlist_matches
            
        except Exception as e:
            logger.error(f"Playlist search failed: {e}")
            return []
    
    def extract_tracks_from_playlist(self, playlist_id: str, playlist_name: str, 
                                   max_tracks: int = 100) -> List[PlaylistTrack]:
        """Extract tracks from a specific playlist"""
        
        if not self.spotify:
            return []
        
        try:
            logger.info(f"   📋 Extracting tracks from: '{playlist_name}'")
            
            # Get tracks from playlist (ensure limit is at least 1)
            tracks = []
            track_limit = max(1, min(50, max_tracks))
            results = self.spotify.playlist_tracks(playlist_id, limit=track_limit)
            
            while results:
                for item in results['items']:
                    if not item or not item.get('track'):
                        continue
                    
                    track = item['track']
                    if not track or not track.get('name') or not track.get('artists'):
                        continue
                    
                    # Extract track information
                    title = track['name']
                    artist = track['artists'][0]['name'] if track['artists'] else "Unknown"
                    album = track.get('album', {}).get('name')
                    spotify_id = track.get('id')
                    popularity = track.get('popularity')
                    
                    tracks.append(PlaylistTrack(
                        title=title,
                        artist=artist,
                        album=album,
                        spotify_id=spotify_id,
                        popularity=popularity,
                        source_playlist=playlist_name
                    ))
                
                # Get next batch if available and we haven't hit max_tracks
                if results['next'] and len(tracks) < max_tracks:
                    results = self.spotify.next(results)
                else:
                    break
            
            self.stats["tracks_extracted"] += len(tracks)
            logger.info(f"      ✅ Extracted {len(tracks)} tracks")
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to extract tracks from playlist {playlist_id}: {e}")
            return []
    
    def discover_candidates_from_playlists(self, theme: str, max_candidates: int = 200,
                                         max_playlists: int = 10, exclude_mainstream: bool = False,
                                         era: str = None, genre: str = None) -> List[Dict[str, str]]:
        """Discover song candidates by searching playlists for the theme"""
        
        if not self.spotify:
            logger.warning("Spotify playlist discovery not available")
            return []
        
        logger.info(f"🎵 Starting playlist-based discovery for: '{theme}'")
        
        # Search for relevant playlists
        playlist_matches = self.search_playlists_for_theme(theme, max_playlists * 2, 
                                                          exclude_mainstream, era, genre)
        
        if not playlist_matches:
            logger.warning("No relevant playlists found")
            return []
        
        # Extract tracks from top playlists
        all_tracks = []
        tracks_per_playlist = max(10, max_candidates // max_playlists)
        
        for playlist in playlist_matches[:max_playlists]:
            tracks = self.extract_tracks_from_playlist(
                playlist.id, 
                playlist.name, 
                tracks_per_playlist
            )
            all_tracks.extend(tracks)
            
            # Stop if we have enough candidates
            if len(all_tracks) >= max_candidates:
                break
        
        # Convert to standard format and remove duplicates
        seen = set()
        candidates = []
        
        for track in all_tracks:
            # Create unique key for deduplication
            key = f"{track.title.lower()}|{track.artist.lower()}"
            
            if key not in seen:
                seen.add(key)
                candidates.append({
                    "title": track.title,
                    "artist": track.artist,
                    "source": f"playlist:{track.source_playlist}"
                })
        
        self.stats["unique_tracks"] = len(candidates)
        
        logger.info(f"✅ Playlist discovery found {len(candidates)} unique candidates")
        
        return candidates[:max_candidates]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        return self.stats.copy()

def main():
    """Test the playlist discovery system"""
    
    logging.basicConfig(level=logging.INFO)
    
    discovery = SpotifyPlaylistDiscovery()
    
    # Test themes
    test_themes = [
        "ominous rock",
        "summer vibes", 
        "dark ambient",
        "workout motivation"
    ]
    
    print("🎵 Spotify Playlist Discovery Test")
    print("=" * 50)
    
    for theme in test_themes:
        print(f"\n🎯 Testing theme: '{theme}'")
        
        candidates = discovery.discover_candidates_from_playlists(theme, max_candidates=20, max_playlists=3)
        
        print(f"Found {len(candidates)} candidates:")
        for i, candidate in enumerate(candidates[:10], 1):  # Show top 10
            print(f"  {i}. {candidate['title']} by {candidate['artist']}")
            print(f"     Source: {candidate['source']}")
    
    # Show statistics
    stats = discovery.get_statistics()
    print(f"\n📊 Discovery Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    main()
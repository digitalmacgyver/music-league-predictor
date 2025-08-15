#!/usr/bin/env ./venv/bin/python3
"""
Spotify Playlist Creator

Creates Spotify playlists from Scout recommendations with proper user authorization.
Handles OAuth flow, playlist creation, track addition, and playlist management.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class PlaylistCreationResult:
    """Result of playlist creation"""
    success: bool
    playlist_id: Optional[str] = None
    playlist_url: Optional[str] = None
    playlist_name: Optional[str] = None
    tracks_added: int = 0
    tracks_failed: int = 0
    error_message: Optional[str] = None
    failed_tracks: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.failed_tracks is None:
            self.failed_tracks = []

class SpotifyPlaylistCreator:
    """Creates and manages Spotify playlists from song recommendations"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, 
                 redirect_uri: str = "http://localhost:8080"):
        """
        Initialize with Spotify credentials
        
        Args:
            client_id: Spotify app client ID (from env if not provided)
            client_secret: Spotify app client secret (from env if not provided)
            redirect_uri: OAuth redirect URI for authorization
        """
        self.client_id = client_id or os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = redirect_uri
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify client ID and secret are required")
        
        # Define required scopes for playlist creation and management
        self.scopes = [
            'playlist-modify-private',    # Create/modify private playlists
            'playlist-modify-public',     # Create/modify public playlists
            'playlist-read-private',      # Read user's private playlists
            'user-read-private',          # Read user profile (for user ID)
            'user-read-email'             # Read user email (for user ID)
        ]
        
        self.spotify = None
        self.user_id = None
        
    def authenticate(self, cache_path: str = ".spotify_cache") -> bool:
        """
        Authenticate with Spotify using OAuth flow
        
        Args:
            cache_path: Path to store OAuth tokens for reuse
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Initialize SpotifyOAuth manager
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=' '.join(self.scopes),
                cache_path=cache_path,
                open_browser=True  # Automatically opens browser for auth
            )
            
            # Initialize Spotify client
            self.spotify = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test authentication and get user info
            user_info = self.spotify.current_user()
            self.user_id = user_info['id']
            
            logger.info(f"Authenticated as Spotify user: {user_info['display_name']} ({self.user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Spotify authentication failed: {e}")
            return False
    
    def search_track(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """
        Search for a track on Spotify
        
        Args:
            title: Song title
            artist: Artist name
            
        Returns:
            Track info dict or None if not found
        """
        if not self.spotify:
            logger.error("Not authenticated with Spotify")
            return None
        
        try:
            # Try exact search first
            query = f'track:"{title}" artist:"{artist}"'
            results = self.spotify.search(q=query, type='track', limit=5)
            
            if results['tracks']['items']:
                return results['tracks']['items'][0]  # Return best match
            
            # Try broader search if exact fails
            query = f'{title} {artist}'
            results = self.spotify.search(q=query, type='track', limit=5)
            
            if results['tracks']['items']:
                # Find best match by comparing normalized names
                title_lower = title.lower()
                artist_lower = artist.lower()
                
                for track in results['tracks']['items']:
                    track_title = track['name'].lower()
                    track_artist = track['artists'][0]['name'].lower()
                    
                    # Simple similarity check
                    if (title_lower in track_title or track_title in title_lower) and \
                       (artist_lower in track_artist or track_artist in artist_lower):
                        return track
                
                # If no good match, return first result
                return results['tracks']['items'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Track search failed for {title} by {artist}: {e}")
            return None
    
    def create_playlist(self, name: str, description: str = "", 
                       public: bool = False, collaborative: bool = False) -> Optional[Dict[str, Any]]:
        """
        Create a new Spotify playlist
        
        Args:
            name: Playlist name
            description: Playlist description
            public: Whether playlist should be public
            collaborative: Whether playlist should be collaborative
            
        Returns:
            Playlist info dict or None if creation failed
        """
        if not self.spotify or not self.user_id:
            logger.error("Not authenticated with Spotify")
            return None
        
        try:
            playlist = self.spotify.user_playlist_create(
                user=self.user_id,
                name=name,
                public=public,
                collaborative=collaborative,
                description=description
            )
            
            logger.info(f"Created playlist: {name} (ID: {playlist['id']})")
            return playlist
            
        except Exception as e:
            logger.error(f"Playlist creation failed: {e}")
            return None
    
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> Tuple[int, int]:
        """
        Add tracks to a playlist
        
        Args:
            playlist_id: Spotify playlist ID
            track_ids: List of Spotify track IDs
            
        Returns:
            Tuple of (successful_adds, failed_adds)
        """
        if not self.spotify:
            logger.error("Not authenticated with Spotify")
            return 0, len(track_ids)
        
        try:
            # Spotify allows max 100 tracks per request
            successful_adds = 0
            failed_adds = 0
            
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                
                try:
                    self.spotify.playlist_add_items(playlist_id, batch)
                    successful_adds += len(batch)
                    logger.debug(f"Added {len(batch)} tracks to playlist")
                except Exception as e:
                    logger.error(f"Failed to add batch of tracks: {e}")
                    failed_adds += len(batch)
            
            return successful_adds, failed_adds
            
        except Exception as e:
            logger.error(f"Failed to add tracks to playlist: {e}")
            return 0, len(track_ids)
    
    def create_playlist_from_recommendations(self, recommendations: List[Dict[str, Any]], 
                                           theme: str, description_suffix: str = "", 
                                           public: bool = False) -> PlaylistCreationResult:
        """
        Create a Spotify playlist from Scout recommendations
        
        Args:
            recommendations: List of song recommendations with 'title' and 'artist'
            theme: Theme name for playlist title
            description_suffix: Additional text for playlist description
            
        Returns:
            PlaylistCreationResult with creation details
        """
        if not self.spotify:
            return PlaylistCreationResult(
                success=False,
                error_message="Not authenticated with Spotify"
            )
        
        # Generate playlist name and description
        timestamp = datetime.now().strftime("%Y-%m-%d")
        playlist_name = f"Music League: {theme} ({timestamp})"
        
        base_description = f"Music League recommendations for theme: {theme}"
        if description_suffix:
            playlist_description = f"{base_description}. {description_suffix}"
        else:
            playlist_description = f"{base_description}. Generated by Scout on {timestamp}."
        
        # Create the playlist
        playlist = self.create_playlist(
            name=playlist_name,
            description=playlist_description,
            public=public,
            collaborative=False
        )
        
        if not playlist:
            return PlaylistCreationResult(
                success=False,
                error_message="Failed to create playlist"
            )
        
        # Search for tracks and collect Spotify IDs
        track_ids = []
        failed_tracks = []
        
        logger.info(f"Searching for {len(recommendations)} tracks...")
        
        for i, rec in enumerate(recommendations):
            title = rec.get('title', '').strip()
            artist = rec.get('artist', '').strip()
            
            if not title or not artist:
                failed_tracks.append({
                    'title': title,
                    'artist': artist,
                    'reason': 'Missing title or artist'
                })
                continue
            
            logger.debug(f"Searching {i+1}/{len(recommendations)}: {title} by {artist}")
            
            track = self.search_track(title, artist)
            if track:
                track_ids.append(track['id'])
                logger.debug(f"  ✅ Found: {track['name']} by {track['artists'][0]['name']}")
            else:
                failed_tracks.append({
                    'title': title,
                    'artist': artist,
                    'reason': 'Not found on Spotify'
                })
                logger.debug(f"  ❌ Not found: {title} by {artist}")
        
        # Add tracks to playlist
        if track_ids:
            successful_adds, failed_adds = self.add_tracks_to_playlist(playlist['id'], track_ids)
        else:
            successful_adds, failed_adds = 0, 0
        
        # Create result
        result = PlaylistCreationResult(
            success=True,
            playlist_id=playlist['id'],
            playlist_url=playlist['external_urls']['spotify'],
            playlist_name=playlist_name,
            tracks_added=successful_adds,
            tracks_failed=len(failed_tracks) + failed_adds,
            failed_tracks=failed_tracks
        )
        
        logger.info(f"Playlist creation complete: {successful_adds} tracks added, "
                   f"{len(failed_tracks)} tracks not found")
        
        return result
    
    def get_user_playlists(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get current user's playlists"""
        if not self.spotify:
            return []
        
        try:
            results = self.spotify.current_user_playlists(limit=limit)
            return results['items']
        except Exception as e:
            logger.error(f"Failed to get user playlists: {e}")
            return []

def main():
    """Test playlist creation functionality"""
    logging.basicConfig(level=logging.INFO)
    
    print("🎵 Spotify Playlist Creator Test")
    print("=" * 50)
    
    # Initialize creator
    try:
        creator = SpotifyPlaylistCreator()
        print("✅ Initialized Spotify Playlist Creator")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Make sure SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are set")
        return
    
    # Authenticate
    print("\n🔐 Authenticating with Spotify...")
    print("This will open a browser window for OAuth authorization")
    
    if not creator.authenticate():
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Test with sample recommendations
    test_recommendations = [
        {"title": "Bohemian Rhapsody", "artist": "Queen"},
        {"title": "Hotel California", "artist": "Eagles"},
        {"title": "Imagine", "artist": "John Lennon"},
        {"title": "Stairway to Heaven", "artist": "Led Zeppelin"},
        {"title": "Nonexistent Song", "artist": "Fake Artist"}  # This should fail
    ]
    
    print(f"\n🎵 Creating test playlist with {len(test_recommendations)} recommendations...")
    
    result = creator.create_playlist_from_recommendations(
        recommendations=test_recommendations,
        theme="Test Theme",
        description_suffix="This is a test playlist created by the Music League Scout system."
    )
    
    if result.success:
        print(f"✅ Playlist created successfully!")
        print(f"   Name: {result.playlist_name}")
        print(f"   URL: {result.playlist_url}")
        print(f"   Tracks added: {result.tracks_added}")
        print(f"   Tracks failed: {result.tracks_failed}")
        
        if result.failed_tracks:
            print(f"\n❌ Failed tracks:")
            for track in result.failed_tracks:
                print(f"   • {track['title']} by {track['artist']} - {track['reason']}")
    else:
        print(f"❌ Playlist creation failed: {result.error_message}")

if __name__ == "__main__":
    main()
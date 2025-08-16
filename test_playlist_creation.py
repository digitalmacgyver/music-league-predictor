#!/usr/bin/env ./venv/bin/python3
"""
Quick test for Spotify playlist creation
"""

from spotify_playlist_creator import SpotifyPlaylistCreator
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_playlist_creation():
    # Sample recommendations to test with
    test_songs = [
        {"title": "Good Vibrations", "artist": "The Beach Boys"},
        {"title": "Summer Breeze", "artist": "Seals and Crofts"},
        {"title": "Cruel Summer", "artist": "Taylor Swift"},
        {"title": "Summer of '69", "artist": "Bryan Adams"},
        {"title": "Summertime", "artist": "DJ Jazzy Jeff & The Fresh Prince"},
    ]
    
    print("🎵 Testing Spotify Playlist Creation")
    print("=" * 50)
    
    # Initialize the playlist creator
    try:
        creator = SpotifyPlaylistCreator()
        print("✅ Spotify credentials found")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nMake sure these are in your .env file:")
        print("  SPOTIFY_CLIENT_ID=...")
        print("  SPOTIFY_CLIENT_SECRET=...")
        return
    
    # Authenticate
    print("\n🔐 Authenticating with Spotify...")
    print("   (Browser will open for authorization)")
    print("   ℹ️  Using local server on http://127.0.0.1:8080")
    if not creator.authenticate():
        print("❌ Authentication failed")
        return
    
    print("✅ Authenticated successfully!")
    
    # Create playlist
    print(f"\n📋 Creating playlist with {len(test_songs)} songs...")
    result = creator.create_playlist_from_recommendations(
        recommendations=test_songs,
        theme="Summer Vibes Test",
        description_suffix="Testing Music League Scout playlist generation",
        public=False
    )
    
    if result.success:
        print(f"\n✅ Playlist created successfully!")
        print(f"   📋 Name: {result.playlist_name}")
        print(f"   🔗 URL: {result.playlist_url}")
        print(f"   🎵 Tracks added: {result.tracks_added}/{len(test_songs)}")
        
        if result.failed_tracks:
            print(f"\n⚠️ Some tracks couldn't be found:")
            for track in result.failed_tracks:
                print(f"   • {track['title']} by {track['artist']}")
    else:
        print(f"\n❌ Playlist creation failed: {result.error_message}")
    
    print("\n" + "=" * 50)
    print("Test complete! Check your Spotify account for the playlist.")

if __name__ == "__main__":
    test_playlist_creation()
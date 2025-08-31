#!/usr/bin/env python3
"""
Debug why Jolene has different Spotify IDs
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from spotify_utils import SpotifyUtils
from forecasting import MusicForecaster
import spotipy

def debug_jolene_spotify_ids():
    """Debug why Jolene has different Spotify track IDs"""
    
    print("Debugging Jolene Spotify ID Mismatch")
    print("=" * 35)
    
    # Check what's in our database
    forecaster = MusicForecaster()
    cursor = forecaster.conn.cursor()
    
    cursor.execute("SELECT title, artist, spotify_url FROM songs WHERE LOWER(title) = 'jolene'")
    db_results = cursor.fetchall()
    
    print("Database entries for 'Jolene':")
    for row in db_results:
        spotify_id = SpotifyUtils.extract_track_id(row['spotify_url'])
        print(f"  📀 {row['title']} by {row['artist']}")
        print(f"     URL: {row['spotify_url']}")
        print(f"     ID:  {spotify_id}")
        print()
    
    # Check what Spotify search returns
    if forecaster.spotify:
        print("Spotify search results for 'Jolene' by 'Dolly Parton':")
        try:
            results = forecaster.spotify.search(q='track:"Jolene" artist:"Dolly Parton"', type='track', limit=5)
            tracks = results.get('tracks', {}).get('items', [])
            
            for i, track in enumerate(tracks, 1):
                print(f"  {i}. {track['name']} by {', '.join([a['name'] for a in track['artists']])}")
                print(f"     ID: {track['id']}")
                print(f"     Album: {track['album']['name']} ({track['album']['release_date']})")
                print(f"     Popularity: {track['popularity']}")
                print()
                
        except Exception as e:
            print(f"Error searching Spotify: {e}")
    
    # Check what our existing Spotify IDs contain
    print(f"Total existing Spotify IDs in cache: {len(forecaster.existing_spotify_ids)}")
    dolly_jolene_id = SpotifyUtils.extract_track_id("https://open.spotify.com/track/2SpEHTbUuebeLkgs9QB7Ue")
    if dolly_jolene_id in forecaster.existing_spotify_ids:
        print(f"✅ Dolly Parton's Jolene ID ({dolly_jolene_id}) IS in existing cache")
    else:
        print(f"❌ Dolly Parton's Jolene ID ({dolly_jolene_id}) NOT in existing cache")

if __name__ == "__main__":
    debug_jolene_spotify_ids()
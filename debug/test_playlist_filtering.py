#!/usr/bin/env python3
"""
Test the enhanced playlist filtering logic
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from playlist_discovery import SpotifyPlaylistDiscovery

def test_playlist_relevance_filtering():
    """Test how playlist relevance changes with different options"""
    
    discovery = SpotifyPlaylistDiscovery()
    
    # Test playlists with mainstream vs alternative characteristics
    test_playlists = [
        ("90s Hits - Top 100 Songs", "The ultimate collection of 90s hits"),
        ("90s Underground Alternative", "Hidden gems from the 90s alternative scene"),
        ("Best of the 90s Billboard Charts", "Top charting songs from the 1990s"),
        ("90s Indie Rock Deep Cuts", "Obscure and cult 90s indie tracks"),
        ("90s Grunge and Alternative", "Essential 90s grunge bands"),
        ("Classic Rock Greatest Hits", "All-time classic rock hits"),
        ("Hip Hop Underground 90s", "90s underground hip hop tracks")
    ]
    
    theme = "90s music"
    
    print("Testing Playlist Relevance Scoring")
    print("=" * 50)
    print(f"Theme: '{theme}'")
    print()
    
    # Test normal mode (no special filtering)
    print("🎵 Normal Mode (no special filtering):")
    for name, desc in test_playlists:
        score = discovery.calculate_playlist_relevance(name, theme, desc)
        print(f"  {score:.2f} - {name}")
    
    print()
    
    # Test exclude mainstream mode
    print("🚫 Exclude Mainstream Mode:")
    for name, desc in test_playlists:
        score = discovery.calculate_playlist_relevance(name, theme, desc, exclude_mainstream=True)
        print(f"  {score:.2f} - {name}")
    
    print()
    
    # Test era filtering
    print("📅 Era Filtering (90s):")
    for name, desc in test_playlists:
        score = discovery.calculate_playlist_relevance(name, theme, desc, era="90s")
        print(f"  {score:.2f} - {name}")
    
    print()
    
    # Test genre filtering
    print("🎸 Genre Filtering (rock):")
    for name, desc in test_playlists:
        score = discovery.calculate_playlist_relevance(name, theme, desc, genre="rock")
        print(f"  {score:.2f} - {name}")
    
    print()
    
    # Test combined filtering
    print("🎯 Combined: Exclude Mainstream + 90s + Rock:")
    for name, desc in test_playlists:
        score = discovery.calculate_playlist_relevance(name, theme, desc, 
                                                     exclude_mainstream=True, 
                                                     era="90s", genre="rock")
        print(f"  {score:.2f} - {name}")
    
    print()
    print("Expected behavior:")
    print("- Mainstream playlists should get lower scores with --exclude-mainstream")
    print("- Underground/indie playlists should get higher scores with --exclude-mainstream") 
    print("- Era mismatches should get penalties")
    print("- Genre matches should get bonuses")

if __name__ == "__main__":
    test_playlist_relevance_filtering()
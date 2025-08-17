#!/usr/bin/env ./venv/bin/python3
"""
Debug the specific "It's Raining Tacos" verification issue
"""

import os
import logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from candidate_verification import CandidateVerifier

load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_spotify_search():
    """Test Spotify search directly"""
    print("🔍 Testing Spotify Search for 'It's Raining Tacos' by Parry Gripp")
    print("=" * 70)
    
    # Initialize Spotify client
    client_credentials_manager = SpotifyClientCredentials(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
    )
    spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    title = "It's Raining Tacos"
    artist = "Parry Gripp"
    
    # Test exact search
    print(f"\n1. Exact search: track:\"{title}\" artist:\"{artist}\"")
    exact_query = f'track:"{title}" artist:"{artist}"'
    exact_results = spotify.search(q=exact_query, type='track', limit=5)
    print(f"   Results: {len(exact_results['tracks']['items'])}")
    
    for i, track in enumerate(exact_results['tracks']['items']):
        print(f"   {i+1}. '{track['name']}' by '{track['artists'][0]['name']}'")
    
    # Test loose search
    print(f"\n2. Loose search: {title} {artist}")
    loose_query = f'{title} {artist}'
    loose_results = spotify.search(q=loose_query, type='track', limit=10)
    print(f"   Results: {len(loose_results['tracks']['items'])}")
    
    for i, track in enumerate(loose_results['tracks']['items']):
        print(f"   {i+1}. '{track['name']}' by '{track['artists'][0]['name']}'")
    
    return exact_results, loose_results

def test_verification_logic():
    """Test the verification logic specifically"""
    print("\n🔧 Testing Verification Logic")
    print("=" * 70)
    
    verifier = CandidateVerifier()
    
    # Test the exact case that's failing
    title = "It's Raining Tacos"
    artist = "Parry Gripp"
    
    print(f"\nTesting verification for: '{title}' by '{artist}'")
    
    validation = verifier.verify_with_spotify(title, artist)
    
    print(f"Result: {validation.is_valid}")
    print(f"Method: {validation.verification_method}")
    print(f"Confidence penalty: {validation.confidence_penalty}")
    print(f"Issues: {validation.issues}")
    
    if validation.is_valid:
        print(f"Verified title: '{validation.verified_title}'")
        print(f"Verified artist: '{validation.verified_artist}'")

def test_normalization():
    """Test the normalization logic"""
    print("\n🧹 Testing Normalization")
    print("=" * 70)
    
    verifier = CandidateVerifier()
    
    # Test title normalization
    titles = [
        "It's Raining Tacos",
        "Raining Tacos",
        "its raining tacos",
        "raining tacos"
    ]
    
    print("Title normalization:")
    for title in titles:
        normalized = verifier.normalize_title(title).lower()
        print(f"  '{title}' -> '{normalized}'")
    
    # Test artist normalization
    artists = [
        "Parry Gripp",
        "parry gripp",
        "PARRY GRIPP"
    ]
    
    print("\nArtist normalization:")
    for artist in artists:
        normalized = verifier.normalize_artist(artist).lower()
        print(f"  '{artist}' -> '{normalized}'")

def test_prefix_logic():
    """Test the prefix removal logic specifically"""
    print("\n🔤 Testing Prefix Removal Logic")
    print("=" * 70)
    
    # Simulate the prefix logic from the verification code
    norm_title = "it's raining tacos"
    track_title = "raining tacos"
    
    print(f"Original title: '{norm_title}'")
    print(f"Track title: '{track_title}'")
    
    # Remove common prefixes
    common_prefixes = ["it's ", "its ", "the ", "a ", "an "]
    title_no_prefix = norm_title
    track_no_prefix = track_title
    
    for prefix in common_prefixes:
        if title_no_prefix.startswith(prefix):
            print(f"  Removing prefix '{prefix}' from title")
            title_no_prefix = title_no_prefix[len(prefix):]
        if track_no_prefix.startswith(prefix):
            print(f"  Removing prefix '{prefix}' from track")
            track_no_prefix = track_no_prefix[len(prefix):]
    
    print(f"Title without prefix: '{title_no_prefix}'")
    print(f"Track without prefix: '{track_no_prefix}'")
    print(f"Match: {title_no_prefix == track_no_prefix}")
    print(f"Length check: {len(title_no_prefix) > 3}")
    
    if title_no_prefix == track_no_prefix and len(title_no_prefix) > 3:
        print("✅ Should match with 0.85 confidence")
    else:
        print("❌ No match")

def main():
    """Run all debug tests"""
    print("🐛 Debugging 'It's Raining Tacos' Verification Issue")
    print("=" * 70)
    
    # Test direct Spotify search
    exact_results, loose_results = test_spotify_search()
    
    # Test normalization
    test_normalization()
    
    # Test prefix logic
    test_prefix_logic()
    
    # Test verification logic
    test_verification_logic()
    
    print("\n" + "=" * 70)
    print("Debug complete!")

if __name__ == "__main__":
    main()
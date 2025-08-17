#!/usr/bin/env python3
"""
Spotify API Setup Guide and Credential Tester

This script helps you set up Spotify API credentials and test the connection.
Unlike Music League cookies, Spotify requires app registration.
"""

import os
import sys
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def print_setup_instructions():
    """Print detailed instructions for setting up Spotify API credentials"""
    print("🎵 SPOTIFY API SETUP GUIDE")
    print("=" * 50)
    print()
    print("To get Spotify API credentials, you need to register an app:")
    print()
    print("1. Go to: https://developer.spotify.com/dashboard")
    print("2. Log in with your Spotify account")
    print("3. Click 'Create an App'")
    print("4. Fill out the form:")
    print("   - App Name: 'Music League Forecaster' (or any name)")
    print("   - App Description: 'Personal tool for analyzing music data'")
    print("   - Redirect URI: http://localhost:8080/callback")
    print("   - Check the boxes for Terms of Service")
    print("5. Click 'Create'")
    print("6. On your app dashboard, click 'Settings'")
    print("7. Copy the 'Client ID' and 'Client Secret'")
    print()
    print("Note: This only requires read access to public Spotify data.")
    print("You don't need premium or special permissions.")
    print()

def open_spotify_dashboard():
    """Open Spotify Developer Dashboard in browser"""
    try:
        webbrowser.open("https://developer.spotify.com/dashboard")
        print("✅ Opened Spotify Developer Dashboard in your browser")
        return True
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print("Please manually visit: https://developer.spotify.com/dashboard")
        return False

def prompt_for_credentials():
    """Interactively prompt for Spotify credentials"""
    print("\n🔑 CREDENTIAL SETUP")
    print("=" * 50)
    
    print("Enter your Spotify app credentials:")
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Both Client ID and Client Secret are required")
        return None, None
    
    return client_id, client_secret

def test_spotify_credentials(client_id, client_secret):
    """Test if the provided credentials work"""
    print("\n🧪 TESTING CREDENTIALS")
    print("=" * 50)
    
    try:
        # Set up Spotify client
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test with a simple search
        print("Testing connection...")
        results = sp.search(q="test", type='track', limit=1)
        
        if results and results['tracks']['items']:
            track = results['tracks']['items'][0]
            print(f"✅ Success! Found track: '{track['name']}' by {track['artists'][0]['name']}")
            
            # Test audio features
            track_id = track['id']
            features = sp.audio_features([track_id])[0]
            if features:
                print(f"✅ Audio features working! Energy: {features['energy']:.2f}, Valence: {features['valence']:.2f}")
            else:
                print("⚠️  Search works but audio features failed")
                
            return True
        else:
            print("❌ Search returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Credential test failed: {e}")
        if "Invalid client" in str(e):
            print("💡 This usually means the Client ID or Client Secret is incorrect")
        elif "unauthorized" in str(e).lower():
            print("💡 This usually means the credentials are wrong or the app needs approval")
        return False

def save_to_env_file(client_id, client_secret):
    """Save credentials to .env file"""
    env_path = Path(".env")
    
    # Read existing .env content if it exists
    existing_content = ""
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Filter out existing Spotify credentials
        filtered_lines = []
        for line in lines:
            if not line.startswith('SPOTIFY_CLIENT_ID=') and not line.startswith('SPOTIFY_CLIENT_SECRET='):
                filtered_lines.append(line)
        
        existing_content = ''.join(filtered_lines)
    
    # Add new Spotify credentials
    spotify_config = f"""
# Spotify Web API credentials
SPOTIFY_CLIENT_ID={client_id}
SPOTIFY_CLIENT_SECRET={client_secret}
"""
    
    # Write the updated .env file
    with open(env_path, 'w') as f:
        f.write(existing_content.rstrip() + spotify_config)
    
    print(f"✅ Credentials saved to {env_path}")
    print("🎵 Spotify features are now enabled for the forecasting system!")

def test_forecasting_system():
    """Test the forecasting system with Spotify credentials"""
    print("\n🔮 TESTING FORECASTING SYSTEM")
    print("=" * 50)
    
    try:
        # Import and test forecasting system
        from forecasting import MusicForecaster
        
        forecaster = MusicForecaster()
        
        if forecaster.spotify is None:
            print("❌ Forecasting system still shows Spotify as unavailable")
            print("💡 Try restarting or check that .env file was saved correctly")
            return False
        
        # Test audio features for a well-known song
        print("Testing audio feature extraction...")
        features = forecaster.get_spotify_features("Bohemian Rhapsody", "Queen")
        
        if features:
            print(f"✅ Success! Bohemian Rhapsody features:")
            print(f"   Energy: {features.energy:.2f}")
            print(f"   Valence: {features.valence:.2f}")
            print(f"   Danceability: {features.danceability:.2f}")
            print(f"   Tempo: {features.tempo:.1f} BPM")
            forecaster.close()
            return True
        else:
            print("❌ Could not get audio features")
            forecaster.close()
            return False
            
    except Exception as e:
        print(f"❌ Forecasting system test failed: {e}")
        return False

def main():
    """Main setup flow"""
    logging.basicConfig(level=logging.INFO)
    
    print_setup_instructions()
    
    # Ask if user wants to open browser
    response = input("Open Spotify Developer Dashboard in browser? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        open_spotify_dashboard()
        print("\nAfter creating your app, come back here to enter credentials...")
        input("Press Enter when ready to continue...")
    
    # Get credentials
    client_id, client_secret = prompt_for_credentials()
    if not client_id or not client_secret:
        print("❌ Setup cancelled")
        return
    
    # Test credentials
    if not test_spotify_credentials(client_id, client_secret):
        print("❌ Credential test failed. Please check your Client ID and Secret.")
        print("💡 Make sure you copied them correctly from the Spotify dashboard")
        return
    
    # Save to .env file
    save_to_env_file(client_id, client_secret)
    
    # Test forecasting system
    test_forecasting_system()
    
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 50)
    print("You can now run predictions with enhanced Spotify audio features:")
    print("  ./venv/bin/python3 predict_food_theme.py")
    print("  ./venv/bin/python3 predict_theme_template.py")

if __name__ == "__main__":
    main()
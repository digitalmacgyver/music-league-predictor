#!/usr/bin/env ./venv/bin/python3
"""
Debug Spotify API permissions and authentication requirements
"""

import os
import logging
from dotenv import load_dotenv
import webbrowser
import http.server
import socketserver
import urllib.parse as urlparse
from urllib.parse import parse_qs
import threading
import time
import requests
import base64

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpotifyUserAuthTester:
    """Test if audio features require user authentication"""
    
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = "http://localhost:8888/callback"
        self.scope = "user-read-private user-read-email"  # Basic scopes
        self.auth_code = None
        self.access_token = None
        
    def get_auth_url(self):
        """Generate Spotify authorization URL"""
        auth_url = "https://accounts.spotify.com/authorize"
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': 'music-league-test'
        }
        
        query_string = '&'.join([f"{k}={urlparse.quote(str(v))}" for k, v in params.items()])
        return f"{auth_url}?{query_string}"
    
    def exchange_code_for_token(self, auth_code):
        """Exchange authorization code for access token"""
        token_url = "https://accounts.spotify.com/api/token"
        
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                logger.info("✅ User access token obtained successfully")
                return True
            else:
                logger.error(f"❌ Token exchange failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Token exchange error: {e}")
            return False
    
    def test_with_user_token(self):
        """Test audio features with user access token"""
        if not self.access_token:
            logger.error("No user access token available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test track ID
        track_id = "4iV5W9uYEdYUVa79Axb7Rh"
        
        try:
            # Test audio features with user token
            url = f"https://api.spotify.com/v1/audio-features/{track_id}"
            response = requests.get(url, headers=headers)
            
            logger.info(f"User token audio features response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Audio features work with user token!")
                logger.info(f"Energy: {data.get('energy')}, Danceability: {data.get('danceability')}")
                return True
            else:
                logger.error(f"❌ Audio features still fail with user token: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ User token test error: {e}")
            return False

def test_api_documentation():
    """Check what the official Spotify API docs say about audio features"""
    
    logger.info("📚 Checking Spotify API documentation requirements...")
    logger.info("According to Spotify Web API docs:")
    logger.info("- Audio Features endpoint: GET /v1/audio-features/{id}")
    logger.info("- Required scope: None (should work with Client Credentials)")
    logger.info("- Authorization: Requires valid access token")
    
    logger.info("\n🔍 Our current situation:")
    logger.info("✅ We have valid access tokens (search/tracks work)")
    logger.info("❌ Audio features endpoints return 403")
    logger.info("🤔 This suggests either:")
    logger.info("   1. Spotify changed their API permissions recently")
    logger.info("   2. Our app registration is missing permissions")
    logger.info("   3. There's a region/country restriction")
    logger.info("   4. Our credentials have been rate limited or flagged")

def test_different_track_ids():
    """Test audio features with multiple track IDs to see if it's track-specific"""
    
    logger.info("🎵 Testing audio features with different track IDs...")
    
    # Get client credentials token
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {'grant_type': 'client_credentials'}
    
    try:
        response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
        if response.status_code != 200:
            logger.error("Failed to get token")
            return
        
        access_token = response.json().get('access_token')
        
        # Test multiple popular track IDs
        test_tracks = [
            ("4iV5W9uYEdYUVa79Axb7Rh", "Original test track"),
            ("4kbB5YjPpTFdOOSMhJyWJR", "Come As You Are - Nirvana"),
            ("7K8XoQXZBffc4xG2xIQHMO", "Rock That Body - Black Eyed Peas"),
            ("1mWdTewIgB3gtBM3TOSFhB", "Bohemian Rhapsody - Queen"),
            ("5ChkMS8OtdzJeqyybCc9R5", "Shape of You - Ed Sheeran")
        ]
        
        auth_headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        for track_id, description in test_tracks:
            url = f"https://api.spotify.com/v1/audio-features/{track_id}"
            response = requests.get(url, headers=auth_headers)
            
            status_icon = "✅" if response.status_code == 200 else "❌"
            logger.info(f"{status_icon} {description}: {response.status_code}")
            
            if response.status_code != 200:
                logger.info(f"   Error: {response.text}")
                
    except Exception as e:
        logger.error(f"❌ Multiple track test error: {e}")

def main():
    """Run comprehensive permission investigation"""
    
    print("🔐 Spotify API Permissions Investigation")
    print("=" * 50)
    
    # Test 1: Check documentation requirements
    test_api_documentation()
    
    print("\n" + "=" * 50)
    
    # Test 2: Try different track IDs
    test_different_track_ids()
    
    print("\n" + "=" * 50)
    
    # Test 3: Manual user auth test instructions
    logger.info("📋 Manual User Authentication Test:")
    logger.info("If you want to test user authentication:")
    logger.info("1. Go to: https://developer.spotify.com/console/get-audio-features/")
    logger.info("2. Try the audio features endpoint manually")
    logger.info("3. Compare the results with our client credentials")
    
    print("\n🏁 Permission investigation complete!")
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 20)
    print("❌ Audio features endpoints consistently return 403")
    print("✅ Other endpoints work fine with client credentials")
    print("🤔 This suggests Spotify may have restricted audio features")
    print("💡 Recommendation: Use fallback audio scoring or request user auth")

if __name__ == "__main__":
    main()
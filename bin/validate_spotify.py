#!/usr/bin/env python3
"""
Spotify API Investigation Tool

Tests Spotify API endpoints with different approaches to diagnose 403 errors
"""

import os
import json
import requests
import base64
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpotifyAPITester:
    """Test Spotify API endpoints with different authentication methods"""
    
    def __init__(self):
        # Load credentials from environment
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables required")
        
        self.base_url = "https://api.spotify.com/v1"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.access_token = None
        
    def get_client_credentials_token(self) -> Optional[str]:
        """Get access token using Client Credentials flow"""
        logger.info("🔑 Requesting access token using Client Credentials flow...")
        
        # Encode credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            logger.info(f"Token request status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                logger.info("✅ Access token obtained successfully")
                logger.info(f"Token type: {token_data.get('token_type', 'Unknown')}")
                logger.info(f"Expires in: {token_data.get('expires_in', 'Unknown')} seconds")
                return self.access_token
            else:
                logger.error(f"❌ Token request failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Token request exception: {e}")
            return None
    
    def test_search_endpoint(self) -> Dict[str, Any]:
        """Test the search endpoint that's been giving us 403s"""
        logger.info("🔍 Testing search endpoint...")
        
        if not self.access_token:
            return {"error": "No access token available"}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test with a simple search query
        params = {
            'q': 'rock',
            'type': 'track',
            'limit': 10
        }
        
        try:
            url = f"{self.base_url}/search"
            response = requests.get(url, headers=headers, params=params)
            
            logger.info(f"Search response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                track_count = len(data.get('tracks', {}).get('items', []))
                logger.info(f"✅ Search successful - found {track_count} tracks")
                return {"success": True, "track_count": track_count, "data": data}
            else:
                logger.error(f"❌ Search failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {"error": f"HTTP {response.status_code}", "response": response.text}
                
        except Exception as e:
            logger.error(f"❌ Search exception: {e}")
            return {"error": str(e)}
    
    def test_audio_features_endpoint(self, track_id: str = "4iV5W9uYEdYUVa79Axb7Rh") -> Dict[str, Any]:
        """Test the audio features endpoint - this is what often gives 403s"""
        logger.info(f"🎵 Testing audio features endpoint for track: {track_id}")
        
        if not self.access_token:
            return {"error": "No access token available"}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Test single track audio features
            url = f"{self.base_url}/audio-features/{track_id}"
            response = requests.get(url, headers=headers)
            
            logger.info(f"Audio features response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Audio features successful")
                logger.info(f"Track features: danceability={data.get('danceability')}, energy={data.get('energy')}")
                return {"success": True, "data": data}
            else:
                logger.error(f"❌ Audio features failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {"error": f"HTTP {response.status_code}", "response": response.text}
                
        except Exception as e:
            logger.error(f"❌ Audio features exception: {e}")
            return {"error": str(e)}
    
    def test_multiple_audio_features(self, track_ids: list = None) -> Dict[str, Any]:
        """Test the batch audio features endpoint"""
        if track_ids is None:
            track_ids = ["4iV5W9uYEdYUVa79Axb7Rh", "1h2xVEoJORqrg71HocgqXd"]
        
        logger.info(f"🎵 Testing batch audio features for {len(track_ids)} tracks")
        
        if not self.access_token:
            return {"error": "No access token available"}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Test batch audio features
            params = {'ids': ','.join(track_ids)}
            url = f"{self.base_url}/audio-features"
            response = requests.get(url, headers=headers, params=params)
            
            logger.info(f"Batch audio features response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                feature_count = len(data.get('audio_features', []))
                logger.info(f"✅ Batch audio features successful - got {feature_count} feature sets")
                return {"success": True, "data": data}
            else:
                logger.error(f"❌ Batch audio features failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {"error": f"HTTP {response.status_code}", "response": response.text}
                
        except Exception as e:
            logger.error(f"❌ Batch audio features exception: {e}")
            return {"error": str(e)}
    
    def test_track_endpoint(self, track_id: str = "4iV5W9uYEdYUVa79Axb7Rh") -> Dict[str, Any]:
        """Test the track info endpoint"""
        logger.info(f"📀 Testing track endpoint for: {track_id}")
        
        if not self.access_token:
            return {"error": "No access token available"}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            url = f"{self.base_url}/tracks/{track_id}"
            response = requests.get(url, headers=headers)
            
            logger.info(f"Track response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Track info successful")
                logger.info(f"Track: {data.get('name')} by {data.get('artists', [{}])[0].get('name', 'Unknown')}")
                return {"success": True, "data": data}
            else:
                logger.error(f"❌ Track info failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {"error": f"HTTP {response.status_code}", "response": response.text}
                
        except Exception as e:
            logger.error(f"❌ Track info exception: {e}")
            return {"error": str(e)}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all endpoint tests and return results"""
        logger.info("🚀 Starting comprehensive Spotify API test...")
        
        results = {
            "token_acquisition": False,
            "search": None,
            "track_info": None,
            "audio_features_single": None,
            "audio_features_batch": None
        }
        
        # Step 1: Get access token
        if self.get_client_credentials_token():
            results["token_acquisition"] = True
            
            # Step 2: Test search endpoint
            results["search"] = self.test_search_endpoint()
            
            # Step 3: Test track info endpoint
            results["track_info"] = self.test_track_endpoint()
            
            # Step 4: Test single audio features
            results["audio_features_single"] = self.test_audio_features_endpoint()
            
            # Step 5: Test batch audio features
            results["audio_features_batch"] = self.test_multiple_audio_features()
        
        return results

def test_different_request_formats():
    """Test different ways of formatting requests to identify the issue"""
    logger.info("🔬 Testing different request formats...")
    
    tester = SpotifyAPITester()
    if not tester.get_client_credentials_token():
        logger.error("Cannot proceed without access token")
        return
    
    track_id = "4iV5W9uYEdYUVa79Axb7Rh"  # Sample track ID
    
    # Test 1: Standard request
    logger.info("Test 1: Standard audio features request")
    result1 = tester.test_audio_features_endpoint(track_id)
    
    # Test 2: Different headers
    logger.info("Test 2: Audio features with different headers")
    headers = {
        'Authorization': f'Bearer {tester.access_token}',
        'Accept': 'application/json',
        'User-Agent': 'Music-League-Scout/1.0'
    }
    
    try:
        url = f"{tester.base_url}/audio-features/{track_id}"
        response = requests.get(url, headers=headers)
        logger.info(f"Alternative headers result: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Alternative headers exception: {e}")
    
    # Test 3: Using requests session
    logger.info("Test 3: Using requests session")
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {tester.access_token}',
        'Content-Type': 'application/json'
    })
    
    try:
        url = f"{tester.base_url}/audio-features/{track_id}"
        response = session.get(url)
        logger.info(f"Session request result: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Session request exception: {e}")

def main():
    """Run the Spotify API validation tests"""
    
    # Check for required environment variables
    if not os.getenv('SPOTIFY_CLIENT_ID') or not os.getenv('SPOTIFY_CLIENT_SECRET'):
        logger.error("❌ SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables are required")
        logger.info("Please set these in your environment or .env file")
        return
    
    print("🎵 Spotify API Validation Tool")
    print("=" * 50)
    
    # Run comprehensive tests
    tester = SpotifyAPITester()
    results = tester.run_comprehensive_test()
    
    # Print summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    print(f"✅ Token Acquisition: {'SUCCESS' if results['token_acquisition'] else 'FAILED'}")
    
    for test_name, result in results.items():
        if test_name == "token_acquisition":
            continue
            
        if result and isinstance(result, dict):
            status = "SUCCESS" if result.get("success") else "FAILED"
            error = result.get("error", "Unknown error")
            print(f"{'✅' if status == 'SUCCESS' else '❌'} {test_name.replace('_', ' ').title()}: {status}")
            if status == "FAILED":
                print(f"   Error: {error}")
    
    # Run additional format tests
    print("\n🔬 Testing different request formats...")
    test_different_request_formats()
    
    print("\n🏁 Spotify API validation complete!")

if __name__ == "__main__":
    main()
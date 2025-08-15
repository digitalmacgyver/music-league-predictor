#!/usr/bin/env ./venv/bin/python3
"""
Debug Spotify API access - test various endpoints to understand permission issues
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

def test_direct_api_calls(access_token):
    """Test direct API calls to understand what's accessible"""
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    base_url = "https://api.spotify.com/v1"
    
    # Test various endpoints
    endpoints_to_test = [
        ("/search?q=beatles&type=artist&limit=1", "Search Artists"),
        ("/search?q=come together&type=track&limit=1", "Search Tracks"),
        ("/artists/3WrFJ7ztbogyGnTHbHJFl2", "Get Artist (The Beatles)"),
        ("/albums/1klALx0u4AavZNEvC4LzTL", "Get Album"),
        ("/tracks/2EqlS6tkEnglzr7tkKAAYD", "Get Track"),
        ("/audio-features/2EqlS6tkEnglzr7tkKAAYD", "Audio Features"),
        ("/audio-analysis/2EqlS6tkEnglzr7tkKAAYD", "Audio Analysis"),
        ("/me", "Current User Profile"),
        ("/me/playlists", "User Playlists"),
    ]
    
    results = {}
    
    for endpoint, description in endpoints_to_test:
        url = base_url + endpoint
        print(f"\n🧪 Testing: {description}")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ SUCCESS")
                data = response.json()
                if 'items' in data:
                    print(f"   Found {len(data['items'])} items")
                elif 'name' in data:
                    print(f"   Name: {data['name']}")
                elif 'energy' in data:
                    print(f"   Energy: {data['energy']}, Valence: {data['valence']}")
                else:
                    print(f"   Response keys: {list(data.keys())}")
                    
            elif response.status_code == 403:
                print("❌ FORBIDDEN (403)")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Raw response: {response.text}")
                    
            elif response.status_code == 401:
                print("❌ UNAUTHORIZED (401)")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Raw response: {response.text}")
                    
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
            results[description] = {
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'url': url
            }
            
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            results[description] = {
                'status_code': None,
                'success': False,
                'error': str(e),
                'url': url
            }
    
    return results

def test_token_info(client_id, client_secret):
    """Get detailed information about the access token"""
    
    print("\n🔍 GETTING ACCESS TOKEN INFO")
    print("=" * 50)
    
    # Get access token manually
    auth_url = "https://accounts.spotify.com/api/token"
    auth_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    try:
        auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)
        print(f"Auth Status Code: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            access_token = token_data['access_token']
            
            print(f"✅ Access Token obtained")
            print(f"Token Type: {token_data.get('token_type', 'unknown')}")
            print(f"Expires In: {token_data.get('expires_in', 'unknown')} seconds")
            print(f"Scope: {token_data.get('scope', 'none specified')}")
            print(f"Token (first 20 chars): {access_token[:20]}...")
            
            return access_token
        else:
            print(f"❌ Failed to get access token")
            print(f"Response: {auth_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception getting token: {e}")
        return None

def check_app_info(client_id):
    """Check what we can learn about the app itself"""
    
    print("\n📱 APP INFORMATION")
    print("=" * 50)
    print(f"Client ID: {client_id}")
    print(f"Client ID Length: {len(client_id)} characters")
    print(f"Looks valid: {'Yes' if len(client_id) == 32 else 'No (should be 32 chars)'}")

def main():
    """Main debugging function"""
    
    # Load environment variables
    load_dotenv()
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    print("🐛 SPOTIFY API DEBUG TOOL")
    print("=" * 50)
    
    if not client_id or not client_secret:
        print("❌ No credentials found in .env file")
        return
    
    # Check app info
    check_app_info(client_id)
    
    # Get access token info
    access_token = test_token_info(client_id, client_secret)
    
    if not access_token:
        print("❌ Cannot proceed without access token")
        return
    
    # Test various API endpoints
    results = test_direct_api_calls(access_token)
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 50)
    
    working_endpoints = [desc for desc, result in results.items() if result['success']]
    failing_endpoints = [desc for desc, result in results.items() if not result['success']]
    
    print(f"✅ Working endpoints ({len(working_endpoints)}):")
    for endpoint in working_endpoints:
        print(f"   - {endpoint}")
    
    print(f"\n❌ Failing endpoints ({len(failing_endpoints)}):")
    for endpoint in failing_endpoints:
        result = results[endpoint]
        status = result.get('status_code', 'Exception')
        print(f"   - {endpoint} (HTTP {status})")
    
    # Analysis
    print(f"\n🤔 ANALYSIS")
    print("=" * 50)
    
    if len(working_endpoints) > 0:
        print("✅ Your credentials work for some endpoints")
        
        if "Audio Features" in failing_endpoints:
            print("❌ Audio Features endpoint is blocked")
            print("💡 This suggests your app may need additional permissions")
            print("💡 Try creating a new app and explicitly request 'Web API' access")
            print("💡 Some apps are created with limited permissions by default")
        
        if "Current User Profile" in failing_endpoints:
            print("✅ Good: User profile fails (expected for client credentials)")
            print("✅ This confirms you're using the right auth flow")
    else:
        print("❌ No endpoints working - credential or network issue")
    
    # Callback URL analysis
    print(f"\n🔗 CALLBACK URL ANALYSIS")
    print("=" * 50)
    print("Callback URL impact: NONE for client credentials flow")
    print("- Client credentials don't use redirect URIs")
    print("- Your callback URL (example.com/callback) is fine")
    print("- Audio features should work regardless of callback URL")
    print("- The 403 error is a permissions issue, not a callback issue")

if __name__ == "__main__":
    main()
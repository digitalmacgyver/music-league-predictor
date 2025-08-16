#!/usr/bin/env ./venv/bin/python3
"""
Simplified Spotify authentication helper with built-in server
"""

import os
import json
import time
import webbrowser
import http.server
import socketserver
import threading
import urllib.parse
import requests
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

class SpotifyAuthHelper:
    """Handle Spotify OAuth with local callback server"""
    
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = "http://127.0.0.1:8080"
        self.auth_code = None
        self.token_data = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify CLIENT_ID and CLIENT_SECRET required in .env")
    
    def start_callback_server(self):
        """Start local server to catch OAuth callback"""
        
        class CallbackHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(handler_self):
                # Parse query parameters
                parsed = urllib.parse.urlparse(handler_self.path)
                params = urllib.parse.parse_qs(parsed.query)
                
                if 'code' in params:
                    self.auth_code = params['code'][0]
                    
                    # Send success page
                    handler_self.send_response(200)
                    handler_self.send_header('Content-type', 'text/html')
                    handler_self.end_headers()
                    
                    html = """
                    <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #1db954;">✅ Success!</h1>
                    <p>Authorization complete. You can close this window.</p>
                    <script>setTimeout(() => window.close(), 3000);</script>
                    </body></html>
                    """
                    handler_self.wfile.write(html.encode())
                else:
                    # Send error page
                    handler_self.send_response(400)
                    handler_self.send_header('Content-type', 'text/html')
                    handler_self.end_headers()
                    handler_self.wfile.write(b"<h1>Error: No authorization code received</h1>")
            
            def log_message(self, format, *args):
                pass  # Suppress logging
        
        # Start server in thread
        def run_server():
            with socketserver.TCPServer(("127.0.0.1", 8080), CallbackHandler) as httpd:
                httpd.handle_request()  # Handle just one request
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(0.5)  # Give server time to start
    
    def get_auth_url(self) -> str:
        """Build Spotify authorization URL"""
        scopes = [
            'playlist-modify-private',
            'playlist-modify-public',
            'playlist-read-private',
            'user-read-private',
            'user-read-email'
        ]
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes)
        }
        
        return f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        
        token_url = "https://accounts.spotify.com/api/token"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Token exchange failed: {response.status_code}")
            print(f"   {response.text}")
            return None
    
    def authenticate(self) -> bool:
        """Complete OAuth flow"""
        
        print("🚀 Starting Spotify authentication...")
        
        # Start callback server
        print("📡 Starting callback server on http://127.0.0.1:8080")
        self.start_callback_server()
        
        # Open browser
        auth_url = self.get_auth_url()
        print("🌐 Opening browser for authorization...")
        print(f"   If browser doesn't open, visit: {auth_url}")
        webbrowser.open(auth_url)
        
        # Wait for callback
        print("⏳ Waiting for authorization (timeout: 2 minutes)...")
        timeout = 120
        start_time = time.time()
        
        while self.auth_code is None and (time.time() - start_time) < timeout:
            time.sleep(0.5)
        
        if not self.auth_code:
            print("❌ Timeout waiting for authorization")
            return False
        
        print(f"✅ Got authorization code!")
        
        # Exchange for token
        print("🔄 Exchanging code for access token...")
        self.token_data = self.exchange_code_for_token(self.auth_code)
        
        if self.token_data:
            # Save token to cache
            cache_file = ".spotify_token_cache"
            with open(cache_file, 'w') as f:
                json.dump(self.token_data, f)
            print(f"✅ Access token obtained and cached!")
            return True
        else:
            print("❌ Failed to get access token")
            return False
    
    def get_cached_token(self) -> Optional[Dict]:
        """Get token from cache if available"""
        cache_file = ".spotify_token_cache"
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None

def main():
    """Test authentication"""
    print("🎵 Spotify Authentication Test")
    print("=" * 50)
    
    try:
        auth = SpotifyAuthHelper()
        
        # Check for cached token
        cached = auth.get_cached_token()
        if cached:
            print("✅ Found cached token")
            print(f"   Token type: {cached.get('token_type')}")
            print(f"   Scope: {cached.get('scope')}")
            print("\nTo re-authenticate, delete .spotify_token_cache")
        else:
            print("No cached token found, starting fresh authentication...")
            if auth.authenticate():
                print("\n✅ Authentication successful!")
                print("   Token saved to .spotify_token_cache")
                print("   You can now create playlists!")
            else:
                print("\n❌ Authentication failed")
                print("   Make sure http://127.0.0.1:8080 is in your Spotify app's redirect URIs")
    
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nMake sure your .env file contains:")
        print("  SPOTIFY_CLIENT_ID=...")
        print("  SPOTIFY_CLIENT_SECRET=...")

if __name__ == "__main__":
    main()
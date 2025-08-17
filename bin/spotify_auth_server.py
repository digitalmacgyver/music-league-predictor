#!/usr/bin/env python3
"""
Simple OAuth callback server for Spotify authentication
Handles the redirect and captures the authorization code
"""

import http.server
import socketserver
import urllib.parse
import threading
import time
import webbrowser
import os
from dotenv import load_dotenv

load_dotenv()

# Global to store the auth code
auth_code = None
server_running = False

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Handle OAuth callback from Spotify"""
    
    def do_GET(self):
        global auth_code
        
        # Parse the URL to get the code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Spotify Authorization Successful</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .container {
                        text-align: center;
                        padding: 2rem;
                        background: rgba(0,0,0,0.3);
                        border-radius: 10px;
                    }
                    h1 { margin-bottom: 1rem; }
                    .emoji { font-size: 3rem; margin: 1rem; }
                    .message { font-size: 1.2rem; margin: 1rem; }
                    .close { 
                        margin-top: 2rem; 
                        padding: 0.5rem 1rem;
                        background: #1db954;
                        border: none;
                        border-radius: 5px;
                        color: white;
                        cursor: pointer;
                        font-size: 1rem;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="emoji">✅</div>
                    <h1>Authorization Successful!</h1>
                    <div class="message">You can close this window and return to the terminal.</div>
                    <div class="message">Your Spotify playlist is being created...</div>
                    <button class="close" onclick="window.close()">Close Window</button>
                </div>
                <script>
                    // Auto-close after 5 seconds
                    setTimeout(() => {
                        window.close();
                    }, 5000);
                </script>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
            
        elif 'error' in params:
            # Handle error case
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authorization Failed</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: #ff4444;
                        color: white;
                    }}
                    .container {{ text-align: center; }}
                    .emoji {{ font-size: 3rem; margin: 1rem; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="emoji">❌</div>
                    <h1>Authorization Failed</h1>
                    <p>Error: {params.get('error', ['Unknown error'])[0]}</p>
                    <p>Please close this window and try again.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
        else:
            # No code or error - shouldn't happen
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Invalid request</h1>")
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server(port=8080):
    """Run the callback server"""
    global server_running
    
    with socketserver.TCPServer(("127.0.0.1", port), OAuthCallbackHandler) as httpd:
        server_running = True
        print(f"📡 Callback server listening on http://127.0.0.1:{port}")
        
        # Handle one request (the callback)
        httpd.handle_request()
        
        server_running = False
        print("✅ Received callback, shutting down server")

def get_spotify_auth_url(client_id, redirect_uri="http://127.0.0.1:8080"):
    """Generate Spotify authorization URL"""
    scopes = [
        'playlist-modify-private',
        'playlist-modify-public', 
        'playlist-read-private',
        'user-read-private',
        'user-read-email'
    ]
    
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': ' '.join(scopes)
    }
    
    base_url = "https://accounts.spotify.com/authorize"
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def authenticate_spotify():
    """Complete Spotify OAuth flow with local server"""
    global auth_code
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    if not client_id:
        print("❌ SPOTIFY_CLIENT_ID not found in .env")
        return None
    
    # Start the callback server in a thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(1)
    
    # Generate and open auth URL
    auth_url = get_spotify_auth_url(client_id)
    print(f"🌐 Opening browser for Spotify authorization...")
    print(f"   If browser doesn't open, visit: {auth_url}")
    webbrowser.open(auth_url)
    
    # Wait for callback (max 2 minutes)
    print("⏳ Waiting for authorization...")
    timeout = 120
    start_time = time.time()
    
    while auth_code is None and (time.time() - start_time) < timeout:
        time.sleep(0.5)
    
    if auth_code:
        print(f"✅ Got authorization code: {auth_code[:10]}...")
        return auth_code
    else:
        print("❌ Timeout waiting for authorization")
        return None

def main():
    """Test the auth server"""
    print("🎵 Spotify OAuth Test with Local Server")
    print("=" * 50)
    
    # Make sure redirect URI is updated in Spotify app
    print("\n⚠️  IMPORTANT: Make sure your Spotify app has this redirect URI:")
    print("   http://127.0.0.1:8080")
    print("\n Press Enter to continue or Ctrl+C to cancel...")
    input()
    
    auth_code = authenticate_spotify()
    
    if auth_code:
        print("\n✅ Authentication successful!")
        print("   You can now use this auth code with Spotify's token exchange")
        print("\nNext steps:")
        print("1. Exchange this code for an access token")
        print("2. Use the access token to create playlists")
    else:
        print("\n❌ Authentication failed")
        print("   Check that your redirect URI is set correctly in Spotify")

if __name__ == "__main__":
    main()
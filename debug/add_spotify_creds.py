#!/usr/bin/env ./venv/bin/python3
"""
Manually add Spotify credentials to .env file
Use this when setup_spotify.py fails but you have valid credentials
"""

from pathlib import Path

def main():
    print("🔑 MANUAL SPOTIFY CREDENTIAL SETUP")
    print("=" * 40)
    
    # Get credentials
    client_id = input("Enter your Spotify Client ID: ").strip()
    client_secret = input("Enter your Spotify Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Both credentials are required")
        return
    
    # Create or update .env file
    env_path = Path(".env")
    
    # Read existing content if it exists
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
    
    # Add Spotify credentials
    spotify_config = f"""
# Spotify Web API credentials
SPOTIFY_CLIENT_ID={client_id}
SPOTIFY_CLIENT_SECRET={client_secret}
"""
    
    # Write the file
    with open(env_path, 'w') as f:
        f.write(existing_content.rstrip() + spotify_config)
    
    print(f"✅ Credentials saved to {env_path}")
    print("\nNow test with: ./validate_spotify.py")

if __name__ == "__main__":
    main()
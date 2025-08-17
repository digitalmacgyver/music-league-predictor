# Spotify Playlist Generation Setup Guide

## Prerequisites
- A Spotify account (free or premium)
- Scout already installed and working

## Step 1: Create a Spotify App

1. **Go to Spotify Developer Dashboard**
   - Visit: https://developer.spotify.com/dashboard
   - Log in with your Spotify account

2. **Create a New App**
   - Click "Create app"
   - Fill in:
     - App name: `Music League Scout` (or any name you prefer)
     - App description: `Personal music recommendation and playlist creation`
     - Redirect URI: `http://localhost:8080` (IMPORTANT: Must match exactly!)
   - Check "I understand and agree to the Spotify Developer Terms of Service"
   - Click "Save"

3. **Get Your Credentials**
   - In your app dashboard, click "Settings"
   - You'll see:
     - **Client ID**: A long string like `abc123def456...`
     - **Client Secret**: Click "View client secret" to reveal

## Step 2: Set Up Your Environment

### Option A: Using Environment Variables (Recommended)

1. **Create or edit `.env` file** in the music_league directory:
```bash
cd ~/coding_projects/music_league
nano .env  # or use your preferred editor
```

2. **Add your credentials**:
```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### Option B: Using setup_spotify.py

Run our setup script:
```bash
./setup_spotify.py
```
This will prompt you for credentials and save them securely.

## Step 3: Test Playlist Creation

### Basic Test
```bash
# Simple test with a few recommendations
./scout.py "Summer vibes" --number 5 --create-playlist
```

### What Will Happen:
1. Scout will find 5 summer songs
2. A browser window will open for Spotify authorization
3. Log in to Spotify and click "Agree" to grant permissions
4. The browser will redirect to localhost:8080 (you'll see an error page - this is normal!)
5. Scout will automatically capture the authorization and continue
6. Your playlist will be created!

### Full Example Commands

```bash
# Create a private playlist with 10 songs
./scout.py "Workout songs" --number 10 --create-playlist

# Create a public playlist with custom description
./scout.py "Chill study music" --number 15 --create-playlist \
  --playlist-public \
  --playlist-description "Perfect background music for studying"

# Create playlist with specific parameters
./scout.py "90s rock hits" --era 90s --genre rock --number 20 \
  --exclude-mainstream --create-playlist

# With verbose output to see what's happening
./scout.py "Jazz classics" --number 8 --create-playlist --verbose
```

## Step 4: Find Your Playlist

After creation, you'll see output like:
```
✅ Playlist created successfully!
   📋 Name: Music League: Summer vibes (2025-08-15)
   🔗 URL: https://open.spotify.com/playlist/37i9dQZF1DX...
   🎵 Tracks added: 5/5
```

Click the URL or:
1. Open Spotify (app or web)
2. Go to "Your Library" → "Playlists"
3. Your new playlist will be at the top!

## Troubleshooting

### "Spotify credentials not found"
- Make sure your `.env` file is in the correct directory
- Check that credentials are correctly formatted (no extra spaces)
- Try running `source .env` before running Scout

### "Authentication failed"
- Verify your Client ID and Secret are correct
- Make sure redirect URI is exactly `http://localhost:8080`
- Try deleting `.spotify_cache` and authenticating again

### "No tracks added to playlist"
- Some songs might not be available on Spotify
- Check verbose output to see which tracks failed
- The playlist will still be created, just empty or partial

### Browser doesn't open
- Copy the URL from the terminal and open manually
- Make sure you're not running in a headless environment

## Security Notes
- Your `.env` file contains secrets - never commit it to git!
- The `.spotify_cache` file contains your access token - also keep private
- Playlists are private by default for your safety

## Advanced: Using Your Own Redirect URI

If you want to use a different redirect URI:
1. Update it in your Spotify app settings
2. Modify the scout command:
```python
# In spotify_playlist_creator.py, change:
redirect_uri: str = "http://localhost:8080"
# To your preferred URI
```

## Rate Limits
- Spotify allows creating many playlists (up to 11,000 per user)
- No strict rate limits for personal use
- Be reasonable with automated creation

Happy playlist creating! 🎵
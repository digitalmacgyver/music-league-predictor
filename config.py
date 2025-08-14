"""
Configuration settings for Music League scraper
"""

import os
from pathlib import Path

# Base configuration
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database configuration
DATABASE_PATH = DATA_DIR / "music_league.db"
SESSION_PATH = DATA_DIR / "session_state.json"

# Music League URLs
ML_BASE_URL = "https://app.musicleague.com"
ML_LOGIN_URL = f"{ML_BASE_URL}/login/"
ML_COMPLETED_URL = f"{ML_BASE_URL}/completed/"

# Scraping configuration
HEADLESS_MODE = False  # Set to False to see browser during auth
PAGE_LOAD_TIMEOUT = 60000  # 60 seconds
NETWORK_IDLE_TIMEOUT = 5000  # 5 seconds for dynamic content
SCROLL_PAUSE_TIME = 2  # Seconds between scroll actions
AUTH_TIMEOUT = 60  # 60 seconds for authentication
MAX_RETRIES = 3
RETRY_DELAY = 5  # Seconds between retries

# Rate limiting
REQUEST_DELAY_MIN = 1  # Minimum seconds between requests
REQUEST_DELAY_MAX = 3  # Maximum seconds between requests

# League filtering
LEAGUE_FILTER = "Bard's Tale"  # Filter for specific leagues
SCRAPE_ALL_LEAGUES = False  # Set to True to scrape all leagues
TEST_MODE = False  # Set to True to test with single league
TEST_LEAGUE = "Bard's Tale 26"  # League to test with

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = DATA_DIR / "scraper.log"

# Browser configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
VIEWPORT = {"width": 1920, "height": 1080}

# Selectors (update these if the site structure changes)
SELECTORS = {
    "spotify_login_button": "button:has-text('Log In with Spotify')",
    "league_tiles": ".league-tile, [data-testid='league-tile']",
    "round_tiles": ".round-tile, [data-testid='round-tile']",
    "song_cards": ".song-card, [data-testid='song-card']",
    "vote_items": ".vote-item, [data-testid='vote-item']",
}
#!/usr/bin/env python3
"""
Standalone authentication script for Music League
Handles Spotify SSO login and saves session cookies for scraper.py to use
"""

import asyncio
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright

from music_league.config import *

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MusicLeagueAuth:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def setup_browser(self):
        """Initialize browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=HEADLESS_MODE,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context_options = {
            'viewport': VIEWPORT,
            'user_agent': USER_AGENT,
            'ignore_https_errors': True
        }
        
        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()
        self.page.set_default_timeout(PAGE_LOAD_TIMEOUT)

    async def check_existing_session(self):
        """Check if we have a valid saved session"""
        if not SESSION_PATH.exists():
            return False
            
        try:
            with open(SESSION_PATH, 'r') as f:
                session_data = json.load(f)
                if 'cookies' in session_data and session_data['cookies']:
                    # Load cookies into current context
                    await self.context.add_cookies(session_data['cookies'])
                    
                    # Test if session is still valid
                    await self.page.goto(ML_COMPLETED_URL, wait_until='domcontentloaded', timeout=15000)
                    await asyncio.sleep(2)
                    
                    page_content = await self.page.content()
                    current_url = self.page.url
                    
                    # Check for authentication indicators
                    if ("Bard's Tale" in page_content or 
                        ('/completed' in current_url and 'login' not in page_content.lower())):
                        print("✓ Existing session is still valid!")
                        return True
                    else:
                        print("Existing session expired, need to re-authenticate")
                        return False
        except Exception as e:
            logger.warning(f"Could not load existing session: {e}")
            return False

    async def authenticate(self):
        """Handle manual authentication"""
        print("\n" + "="*70)
        print("MUSIC LEAGUE AUTHENTICATION")
        print("="*70)
        print("Please complete authentication in the browser window:")
        print("")
        print("1. Complete the Spotify SSO login process")
        print("2. Ensure you reach the completed leagues page")
        print("3. Verify you can see your 'Bard's Tale' leagues")
        print("4. Return here and press Enter when ready")
        print("="*70 + "\n")
        
        # Navigate to login page
        try:
            await self.page.goto(ML_LOGIN_URL, wait_until='domcontentloaded', timeout=30000)
            logger.info(f"Opened login page: {self.page.url}")
        except Exception as e:
            logger.warning(f"Could not navigate to login page: {e}")
            print("Trying to open completed page directly...")
            await self.page.goto(ML_COMPLETED_URL, wait_until='domcontentloaded', timeout=30000)
        
        # Wait for user confirmation
        input("Press Enter when you have completed login and are on the completed leagues page...")
        
        # Verify authentication by checking for user's content
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"Verifying authentication (attempt {attempt + 1}/{max_attempts})...")
            
            try:
                # Get current page state
                current_url = self.page.url
                page_content = await self.page.content()
                
                print(f"Current URL: {current_url}")
                
                # Primary check: Look for "Bard's Tale" in page content
                if "Bard's Tale" in page_content:
                    print("✓ Found 'Bard's Tale' leagues - authentication successful!")
                    await self.save_session()
                    return True
                
                # Secondary check: Look for other indicators
                if ('/completed' in current_url and 
                    'login' not in page_content.lower() and
                    len(page_content) > 10000):  # Substantial content
                    print("✓ On completed page with content - authentication likely successful!")
                    await self.save_session()
                    return True
                
                # If we're on login/auth pages, definitely not authenticated
                if any(path in current_url for path in ['/login', '/authorize', 'accounts.spotify.com']):
                    print("✗ Still on authentication page")
                else:
                    print("✗ Could not verify authentication")
                    print(f"Page content length: {len(page_content)} characters")
                    if len(page_content) < 1000:
                        print("Page content seems minimal - may not be fully loaded")
                
                if attempt < max_attempts - 1:
                    print("\nPlease ensure you:")
                    print("1. Have successfully logged in with Spotify")
                    print("2. Are on https://app.musicleague.com/completed/")
                    print("3. Can see your completed leagues")
                    input("Press Enter to check again...")
                
            except Exception as e:
                logger.error(f"Error during authentication check: {e}")
                if attempt < max_attempts - 1:
                    input("Error occurred. Please try again - Press Enter...")
        
        print("✗ Authentication verification failed after multiple attempts")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged in to Music League")
        print("2. Navigate to https://app.musicleague.com/completed/")
        print("3. Verify you can see your leagues")
        print("4. Try running this script again")
        return False

    async def save_session(self):
        """Save session cookies and state"""
        try:
            storage_state = await self.context.storage_state()
            SESSION_PATH.parent.mkdir(exist_ok=True)
            with open(SESSION_PATH, 'w') as f:
                json.dump(storage_state, f, indent=2)
            print(f"✓ Session saved to {SESSION_PATH}")
            logger.info("Session saved successfully")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            print(f"✗ Failed to save session: {e}")

    async def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()

async def main():
    print("="*70)
    print("MUSIC LEAGUE LOGIN UTILITY")
    print("="*70)
    
    auth = MusicLeagueAuth()
    
    try:
        await auth.setup_browser()
        
        # Check if we already have a valid session
        if await auth.check_existing_session():
            print("You're already authenticated! Session is valid.")
            print("You can now run ./scraper.py to collect data.")
            return
        
        # Perform authentication
        if await auth.authenticate():
            print("\n" + "="*70)
            print("AUTHENTICATION SUCCESSFUL!")
            print("="*70)
            print("Your session has been saved.")
            print("You can now run ./scraper.py to collect Music League data.")
            print("This login session will persist until it expires.")
        else:
            print("\n" + "="*70)
            print("AUTHENTICATION FAILED")
            print("="*70)
            print("Please try running this script again.")
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error occurred: {e}")
    finally:
        await auth.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
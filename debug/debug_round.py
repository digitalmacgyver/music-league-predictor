#!/usr/bin/env ./venv/bin/python3
"""
Debug script to investigate round page structure
"""

import asyncio
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

from config import *

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoundDebugger:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def setup_browser(self):
        """Initialize browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        
        # Load saved session
        context_options = {
            'viewport': VIEWPORT,
            'user_agent': USER_AGENT,
            'ignore_https_errors': True
        }
        
        if SESSION_PATH.exists():
            with open(SESSION_PATH, 'r') as f:
                session_data = json.load(f)
                if 'cookies' in session_data:
                    context_options['storage_state'] = session_data
        
        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)

    async def debug_round_page(self, round_url):
        """Debug a specific round page structure"""
        print("="*70)
        print(f"DEBUGGING ROUND PAGE: {round_url}")
        print("="*70)
        
        try:
            await self.page.goto(round_url, wait_until='domcontentloaded')
            await asyncio.sleep(5)  # Wait for content to load
            
            content = await self.page.content()
            print(f"Round page content length: {len(content)}")
            print(f"Current URL: {self.page.url}")
            print(f"Page title: {await self.page.title()}")
            
            # Look for songs/tracks structure
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for song-related selectors
            print("\nSearching for song elements with different selectors:")
            
            song_selectors = [
                '.song',
                '.song-card',
                '.song-tile', 
                '.song-item',
                '.track',
                '.track-card',
                '.submission',
                '.submission-card',
                '[class*="song"]',
                '[class*="track"]',
                '[class*="submission"]',
                '[data-testid*="song"]',
                '[data-testid*="track"]',
                '[data-testid*="submission"]'
            ]
            
            for selector in song_selectors:
                try:
                    elements = soup.select(selector)
                    if elements:
                        print(f"  {selector}: {len(elements)} elements")
                        for j, elem in enumerate(elements[:3]):
                            text = elem.get_text(strip=True)[:100]
                            print(f"    {j+1}. '{text}...'")
                except Exception as e:
                    print(f"  {selector}: Error - {e}")
            
            # Look for text patterns
            print(f"\nText analysis:")
            text_patterns = ['song', 'track', 'artist', 'album', 'votes', 'points']
            for pattern in text_patterns:
                count = content.lower().count(pattern)
                print(f"'{pattern}' occurrences: {count}")
            
            # Look for specific vote/point patterns
            vote_patterns = [
                r'\d+\s*points?',
                r'\d+\s*votes?',
                r'submitted by',
                r'by\s+\w+',
                r'\d+\s*/\s*\d+'
            ]
            
            print(f"\nVote patterns:")
            for pattern in vote_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                print(f"'{pattern}': {len(matches)} matches")
                if matches:
                    print(f"  Examples: {matches[:3]}")
            
            # Check for any list structures (songs are likely in lists)
            print(f"\nList structures:")
            lists = soup.find_all(['ul', 'ol'])
            print(f"Lists found: {len(lists)}")
            
            for i, lst in enumerate(lists[:5]):
                items = lst.find_all('li')
                if items:
                    print(f"  List {i+1}: {len(items)} items")
                    if items:
                        sample_text = items[0].get_text(strip=True)[:50]
                        print(f"    Sample: '{sample_text}...'")
            
            # Check for table structures (votes might be in tables)
            tables = soup.find_all('table')
            print(f"Tables found: {len(tables)}")
            
            for i, table in enumerate(tables[:3]):
                rows = table.find_all('tr')
                print(f"  Table {i+1}: {len(rows)} rows")
                if rows:
                    cells = rows[0].find_all(['td', 'th'])
                    print(f"    Columns: {len(cells)}")
            
            # Save the round page HTML for manual inspection
            round_id = round_url.split('/')[-2]
            debug_file = Path("data") / f"debug_round_{round_id}.html"
            with open(debug_file, 'w') as f:
                f.write(content)
            print(f"\nRound page HTML saved to: {debug_file}")
            
        except Exception as e:
            print(f"Error loading round page: {e}")

    async def cleanup(self):
        if self.browser:
            await self.browser.close()

async def main():
    debugger = RoundDebugger()
    
    try:
        await debugger.setup_browser()
        
        # Debug first round of Bard's Tale 26
        round_url = "https://app.musicleague.com/l/85191779017d4150b28cc5a67946d57c/0d6b63dd29064dd0afe0ddab5861c0ba/"
        await debugger.debug_round_page(round_url)
        
        print("\n" + "="*70)
        print("ROUND DEBUG COMPLETE")
        print("="*70)
        
    except Exception as e:
        logger.error(f"Debug error: {e}")
    finally:
        await debugger.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
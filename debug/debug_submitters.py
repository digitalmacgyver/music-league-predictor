#!/usr/bin/env ./venv/bin/python3
"""
Debug script to examine song card HTML structure for submitter information
"""

import asyncio
import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from config import SESSION_PATH, ML_BASE_URL

async def debug_submitter_structure():
    """Debug the HTML structure of song cards to find submitter information"""
    
    # Round 6 URL (70s theme)
    round_url = "https://app.musicleague.com/l/85191779017d4150b28cc5a67946d57c/0d6b63dd29064dd0afe0ddab5861c0ba/"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    
    # Load session
    with open(SESSION_PATH, 'r') as f:
        session_data = json.load(f)
    
    context = await browser.new_context(storage_state=session_data)
    page = await context.new_page()
    
    print(f"Loading round page: {round_url}")
    await page.goto(round_url, wait_until='networkidle')
    await asyncio.sleep(3)
    
    # Get page content
    content = await page.content()
    soup = BeautifulSoup(content, 'lxml')
    
    # Find all cards first, then look for Spotify links anywhere
    all_cards = soup.find_all('div', class_='card')
    print(f"Found {len(all_cards)} total cards")
    
    # Find all Spotify links to understand structure
    spotify_links = soup.find_all('a', href=re.compile('spotify.com/track'))
    print(f"Found {len(spotify_links)} Spotify links")
    
    # Process the first few Spotify links and their parent containers
    for i, spotify_link in enumerate(spotify_links[:3]):
        print(f"\n{'='*80}")
        print(f"SPOTIFY LINK {i+1}")
        print(f"{'='*80}")
        
        song_title = spotify_link.get_text(strip=True)
        print(f"Song: {song_title}")
        
        # Find the containing card
        card = spotify_link.find_parent('div', class_='card')
        if not card:
            print("No parent card found!")
            continue
            
        # Print all text content to find submitter
        print("\nAll text content:")
        print("-" * 40)
        all_text = card.get_text(separator=' | ', strip=True)
        print(all_text)
        
        # Look for specific patterns that might indicate submitter
        print("\nDetailed HTML structure:")
        print("-" * 40)
        print(card.prettify()[:1500] + "..." if len(str(card)) > 1500 else card.prettify())
        
        # Look for common submitter patterns
        possible_submitters = []
        
        # Check for user names in various elements
        for elem in card.find_all(['p', 'span', 'div', 'small', 'a']):
            text = elem.get_text(strip=True)
            if text and len(text) > 2 and len(text) < 50:
                # Skip obvious non-names
                if not any(skip in text.lower() for skip in [
                    'spotify', 'vote', 'voter', 'from', 'track', 'album', 
                    'play', 'song', 'music', 'artist', 'feat', 'points', 'listen'
                ]):
                    # Look for name-like patterns (Title Case, multiple words)
                    if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', text):
                        possible_submitters.append(f"'{text}' in {elem.name} with classes {elem.get('class', [])}")
        
        if possible_submitters:
            print(f"\nPossible submitters found:")
            for submitter in possible_submitters:
                print(f"  - {submitter}")
        else:
            print("\nNo obvious submitter names found")
            
        # Also look for specific known submitter "Ben Hamilton" to see where it appears
        if "Ben Hamilton" in all_text:
            print(f"\n*** Found 'Ben Hamilton' in card text! ***")
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_submitter_structure())
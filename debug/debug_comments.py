#!/usr/bin/env ./venv/bin/python3
"""
Debug script to examine exact structure of submitter comments
"""

import asyncio
import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from config import SESSION_PATH

async def debug_comment_structure():
    """Debug the exact HTML structure for submitter comments"""
    
    # Round 6 URL (70s theme) 
    round_url = "https://app.musicleague.com/l/85191779017d4150b28cc5a67946d57c/0d6b63dd29064dd0afe0ddab5861c0ba/"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    
    # Load session
    with open(SESSION_PATH, 'r') as f:
        session_data = json.load(f)
    
    context = await browser.new_context(storage_state=session_data)
    page = await context.new_page()
    
    print(f"Loading round page: {round_url}")
    await page.goto(round_url, wait_until='networkidle')
    
    # Wait for songs to load - look for a specific element
    print("Waiting for songs to load...")
    try:
        await page.wait_for_selector('a[href*="spotify.com/track"]', timeout=10000)
        print("Songs loaded!")
    except:
        print("Timeout waiting for songs")
    
    await asyncio.sleep(2)
    
    # Get page content
    content = await page.content()
    soup = BeautifulSoup(content, 'lxml')
    
    # Check if we have any content
    print(f"Page content length: {len(content)}")
    
    # Look for all Spotify links first
    all_spotify = soup.find_all('a', href=re.compile('spotify.com/track'))
    print(f"Found {len(all_spotify)} Spotify links")
    if all_spotify:
        print("First few songs found:")
        for link in all_spotify[:3]:
            print(f"  - {link.get_text(strip=True)}")
    
    # Find the Sundown song specifically - look for the Spotify link
    sundown_link = soup.find('a', href=re.compile('spotify.com/track/0SjnBEHZVXgCKvOrpvzL2k'))
    if not sundown_link:
        # Try finding by text content
        sundown_link = soup.find('a', string=re.compile('Sundown'))
    if not sundown_link:
        print("Could not find Sundown song!")
        # Try to find any Spotify link to debug
        any_spotify = soup.find('a', href=re.compile('spotify.com/track'))
        if any_spotify:
            print(f"Found a different song: {any_spotify.get_text(strip=True)}")
            sundown_link = any_spotify
        else:
            return
        
    # Get the parent card
    card = sundown_link.find_parent('div', class_='card')
    if not card:
        print("Could not find parent card!")
        return
    
    print("Found Sundown card")
    print("="*80)
    
    # Find the ranking section
    ranking_section = card.find('div', class_=re.compile(r'rank-\d+'))
    if ranking_section:
        print("Found ranking section")
        
        # Get the card body within the ranking section
        ranking_body = ranking_section.find('div', class_='card-body')
        if ranking_body:
            print("\nRanking body HTML:")
            print("-"*40)
            print(ranking_body.prettify())
            
            # Look for all divs with col class
            col_divs = ranking_body.find_all('div', class_=re.compile('col'))
            for i, col_div in enumerate(col_divs):
                print(f"\nCol div {i+1}:")
                print("-"*40)
                print(f"Classes: {col_div.get('class', [])}")
                print(f"Text: {col_div.get_text(strip=True)[:200]}...")
                
                # Check for nested structure
                nested_divs = col_div.find_all('div', recursive=False)
                if nested_divs:
                    print(f"Has {len(nested_divs)} nested divs")
                
                # Check for paragraphs
                paragraphs = col_div.find_all('p')
                if paragraphs:
                    print(f"Has {len(paragraphs)} paragraphs")
                    for j, p in enumerate(paragraphs):
                        print(f"  P{j+1}: {p.get_text(strip=True)[:100]}...")
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_comment_structure())
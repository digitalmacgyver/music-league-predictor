#!/usr/bin/env ./venv/bin/python3
"""
Debug script to examine the DOM structure of vote elements to understand 
how voter names and comments are structured in the HTML
"""

import asyncio
import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from config import SESSION_PATH

async def debug_vote_dom_structure():
    """Debug the actual DOM structure of votes"""
    
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
    
    # Ensure comments are shown
    try:
        show_button = await page.query_selector("button:has-text('Show comments')")
        if show_button:
            await show_button.click()
            await asyncio.sleep(2)
    except:
        pass
    
    content = await page.content()
    soup = BeautifulSoup(content, 'lxml')
    
    # Find the Sundown song card
    sundown_card = None
    for card in soup.find_all('div', class_='card'):
        spotify_link = card.find('a', href=re.compile('spotify.com/track'))
        if spotify_link and 'sundown' in spotify_link.get_text().lower():
            sundown_card = card
            break
    
    if sundown_card:
        print("Found Sundown card!")
        print("="*80)
        
        # Find the card-footer
        card_footer = sundown_card.find('div', class_='card-footer')
        if card_footer:
            print("Card footer HTML structure:")
            print("-" * 40)
            print(card_footer.prettify()[:2000])
            
            # Look for voter names in <b> tags
            voter_names = card_footer.find_all('b')
            print(f"\nFound {len(voter_names)} <b> tags (potential voter names):")
            for i, name_tag in enumerate(voter_names):
                print(f"  {i+1}: '{name_tag.get_text(strip=True)}'")
            
            # Look for comments in <span> tags  
            comment_spans = card_footer.find_all('span')
            print(f"\nFound {len(comment_spans)} <span> tags (potential comments):")
            for i, span in enumerate(comment_spans[:10]):  # Show first 10
                text = span.get_text(strip=True)
                if len(text) > 10:  # Only show substantial content
                    print(f"  {i+1}: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            
            # Look for vote structure patterns
            print("\nLooking for vote structure patterns...")
            
            # Check if votes are in a specific container
            vote_containers = card_footer.find_all(['div', 'li', 'p'])
            vote_count = 0
            for container in vote_containers:
                # Look for containers that have both a name and points
                b_tag = container.find('b')
                span_tag = container.find('span', class_=re.compile('text-break'))
                points_text = container.get_text()
                
                if b_tag and re.search(r'\d+', points_text):
                    vote_count += 1
                    voter_name = b_tag.get_text(strip=True)
                    comment = span_tag.get_text(strip=True) if span_tag else ""
                    points_match = re.search(r'(\d+)', points_text)
                    points = points_match.group(1) if points_match else "?"
                    
                    print(f"Vote {vote_count}: {voter_name} | {points} pts | '{comment[:50]}{'...' if len(comment) > 50 else ''}'")
                    
                    if vote_count >= 5:  # Show first 5 votes
                        break
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_vote_dom_structure())
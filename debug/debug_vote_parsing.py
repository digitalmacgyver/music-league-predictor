#!/usr/bin/env ./venv/bin/python3
"""
Parse the actual vote data structure from the Sundown card
"""

import asyncio
import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from config import SESSION_PATH

def parse_vote_data(footer_text):
    """Parse the vote data from card-footer text"""
    print("Raw footer text:")
    print(repr(footer_text))
    print("\n" + "="*60)
    
    # The format appears to be: voter | comment | points | voter | comment | points...
    # Let's split by | and group into triplets
    parts = [p.strip() for p in footer_text.split('|')]
    print(f"Split into {len(parts)} parts:")
    for i, part in enumerate(parts):
        print(f"  {i}: '{part}'")
    
    votes = []
    i = 0
    while i < len(parts):
        # Look for a pattern: voter_name | optional_comment | points
        if i + 2 < len(parts):
            voter = parts[i]
            comment_or_points = parts[i + 1]
            next_part = parts[i + 2]
            
            # Check if comment_or_points is actually points (just a number)
            if re.match(r'^\d+$', comment_or_points.strip()):
                # No comment, just points
                points = int(comment_or_points)
                comment = ""
                i += 2
            elif re.match(r'^\d+$', next_part.strip()):
                # Has comment and points
                comment = comment_or_points
                points = int(next_part)
                i += 3
            else:
                # Unclear pattern, skip
                i += 1
                continue
                
            votes.append({
                'voter': voter,
                'comment': comment,
                'points': points
            })
        else:
            break
    
    return votes

async def debug_detailed_parsing():
    """Debug detailed vote parsing"""
    
    round_url = "https://app.musicleague.com/l/85191779017d4150b28cc5a67946d57c/0d6b63dd29064dd0afe0ddab5861c0ba/"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    
    with open(SESSION_PATH, 'r') as f:
        session_data = json.load(f)
    
    context = await browser.new_context(storage_state=session_data)
    page = await context.new_page()
    
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
    
    # Find Sundown card
    sundown_card = None
    for card in soup.find_all('div', class_='card'):
        spotify_link = card.find('a', href=re.compile('spotify.com/track'))
        if spotify_link and 'sundown' in spotify_link.get_text().lower():
            sundown_card = card
            break
    
    if sundown_card:
        print("Analyzing Sundown card in detail...")
        
        # 1. Extract submitter comment
        submitter_comment_containers = sundown_card.find_all(['div', 'p'], class_=['card-body', 'bg-body-tertiary'])
        print("\nSubmitter comment containers:")
        for i, container in enumerate(submitter_comment_containers):
            text = container.get_text(strip=True)
            if len(text) > 50 and "canada" in text.lower():
                print(f"Found submitter comment: {text}")
        
        # 2. Extract vote data from card-footer
        card_footer = sundown_card.find('div', class_='card-footer')
        if card_footer:
            footer_text = card_footer.get_text(separator='|', strip=True)
            print(f"\nCard footer text: {footer_text}")
            
            votes = parse_vote_data(footer_text)
            print(f"\nParsed {len(votes)} votes:")
            total_points = 0
            for vote in votes:
                print(f"  {vote['voter']}: {vote['points']} points - '{vote['comment']}'")
                total_points += vote['points']
            
            print(f"\nTotal points calculated: {total_points}")
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_detailed_parsing())
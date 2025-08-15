#!/usr/bin/env ./venv/bin/python3
"""
Debug script to investigate vote parsing and submitter comments
with dynamic show/hide comments functionality
"""

import asyncio
import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from config import SESSION_PATH

async def debug_vote_parsing():
    """Debug vote parsing and submitter comments with show/hide toggle"""
    
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
    
    # First, check if we can find the show/hide comments toggle
    print("Looking for show/hide comments toggle...")
    
    # Try the provided selector first
    toggle_selector = "body > div:nth-child(1) > div > div > div > div.container.my-4 > div:nth-child(2) > div > div.row.gx-2.mb-4.justify-content-center > div:nth-child(1) > button > span"
    
    try:
        toggle_element = await page.query_selector(toggle_selector)
        if toggle_element:
            toggle_text = await toggle_element.inner_text()
            print(f"Found toggle element with text: '{toggle_text}'")
        else:
            print("Toggle element not found with provided selector")
    except Exception as e:
        print(f"Error finding toggle: {e}")
    
    # Try alternative selectors for the toggle button
    alternative_selectors = [
        "button[class*='btn']",
        "button:has-text('comment')",
        "button:has-text('Comment')",
        "span:has-text('comment')",
        "span:has-text('Comment')",
        "[class*='comment']",
    ]
    
    print("\nTrying alternative selectors...")
    for selector in alternative_selectors:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector '{selector}'")
                for i, elem in enumerate(elements[:3]):  # Check first 3
                    text = await elem.inner_text()
                    if 'comment' in text.lower():
                        print(f"  Element {i+1}: '{text}'")
        except Exception as e:
            continue
    
    # Look at the page structure to understand the current state
    print("\nAnalyzing current page structure...")
    content = await page.content()
    soup = BeautifulSoup(content, 'lxml')
    
    # Look for elements that might contain the toggle
    potential_toggles = soup.find_all(['button', 'span', 'a'], string=re.compile(r'comment', re.IGNORECASE))
    print(f"Found {len(potential_toggles)} potential toggle elements containing 'comment'")
    
    for i, elem in enumerate(potential_toggles):
        print(f"Toggle {i+1}: {elem.name} - '{elem.get_text(strip=True)}' - classes: {elem.get('class', [])}")
    
    # Check for card-footer elements and their current state
    card_footers = soup.find_all('div', class_='card-footer')
    print(f"\nFound {len(card_footers)} card-footer elements")
    
    if card_footers:
        for i, footer in enumerate(card_footers[:3]):
            classes = footer.get('class', [])
            has_show = 'show' in classes
            style = footer.get('style', '')
            print(f"Footer {i+1}: classes={classes}, has_show={has_show}, style='{style}'")
    
    # Try to find and click the show comments button if it exists
    show_comments_clicked = False
    
    # Try clicking elements that might be the show comments toggle
    show_patterns = [
        "Show comments",
        "show comments", 
        "Show Comments",
        "SHOW COMMENTS"
    ]
    
    for pattern in show_patterns:
        try:
            # Try to find and click the button
            button = await page.query_selector(f"button:has-text('{pattern}')")
            if not button:
                button = await page.query_selector(f"span:has-text('{pattern}')")
            
            if button:
                print(f"Found and clicking '{pattern}' button...")
                await button.click()
                await asyncio.sleep(2)  # Wait for dynamic content to load
                show_comments_clicked = True
                break
        except Exception as e:
            print(f"Error clicking '{pattern}': {e}")
            continue
    
    if not show_comments_clicked:
        print("Could not find or click show comments button, proceeding with current state...")
    
    # Now analyze the page content for votes and comments
    print("\n" + "="*80)
    print("ANALYZING SONG CARDS FOR VOTES AND COMMENTS")
    print("="*80)
    
    # Refresh content after potential click
    content = await page.content()
    soup = BeautifulSoup(content, 'lxml')
    
    # Find all song cards
    song_cards = soup.find_all('div', class_='card')
    print(f"Found {len(song_cards)} total cards")
    
    # Look specifically for the Sundown song
    sundown_card = None
    for card in song_cards:
        spotify_link = card.find('a', href=re.compile('spotify.com/track'))
        if spotify_link and 'sundown' in spotify_link.get_text().lower():
            sundown_card = card
            break
    
    if sundown_card:
        print("\nFound Sundown card!")
        print("-" * 40)
        
        # Check for card-footer in this specific card
        card_footer = sundown_card.find('div', class_='card-footer')
        if card_footer:
            print("Found card-footer in Sundown card")
            print(f"Footer classes: {card_footer.get('class', [])}")
            print(f"Footer style: {card_footer.get('style', '')}")
            
            # Get all text content from footer
            footer_text = card_footer.get_text(separator=' | ', strip=True)
            print(f"Footer text content: {footer_text}")
            
            # Look for submitter comment pattern
            if "gordon lightfoot" in footer_text.lower() or "canada" in footer_text.lower():
                print("*** Found potential submitter comment in footer! ***")
            
        # Also check for other potential comment containers
        comment_containers = sundown_card.find_all(['div', 'p'], class_=re.compile(r'comment|text|body'))
        print(f"\nFound {len(comment_containers)} potential comment containers in Sundown card")
        
        for i, container in enumerate(comment_containers):
            text = container.get_text(strip=True)
            if len(text) > 20:  # Only show substantial text
                print(f"Container {i+1}: {container.name}.{container.get('class', [])} - {text[:100]}...")
        
        # Look for vote-related elements
        vote_elements = sundown_card.find_all(['div', 'span', 'p'], string=re.compile(r'\d+\s*(point|vote)', re.IGNORECASE))
        print(f"\nFound {len(vote_elements)} potential vote elements")
        
        for i, vote_elem in enumerate(vote_elements):
            print(f"Vote {i+1}: {vote_elem.get_text(strip=True)}")
    
    else:
        print("Could not find Sundown card!")
        
        # Show first few cards for debugging
        print("\nFirst few song cards found:")
        for i, card in enumerate(song_cards[:3]):
            spotify_link = card.find('a', href=re.compile('spotify.com/track'))
            if spotify_link:
                song_title = spotify_link.get_text(strip=True)
                print(f"Card {i+1}: {song_title}")
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_vote_parsing())
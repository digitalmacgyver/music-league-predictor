#!/usr/bin/env ./venv/bin/python3
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import re

async def main():
    # Load session
    with open('data/session_state.json', 'r') as f:
        session_data = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            storage_state=session_data
        )
        page = await context.new_page()
        
        # Go to Bard's Tale 26
        url = "https://app.musicleague.com/l/85191779017d4150b28cc5a67946d57c/"
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(5)  # Wait longer for dynamic content
        
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        # Debug - save full page
        with open('data/debug_full_page.html', 'w') as f:
            f.write(content)
        print("Saved full page to data/debug_full_page.html")
        
        # Look for any divs
        all_divs = soup.find_all('div')
        print(f"Found {len(all_divs)} div elements total")
        
        # Look for any elements with 'card' in class
        card_like = soup.find_all(attrs={'class': re.compile('card', re.I)})
        print(f"Found {len(card_like)} elements with 'card' in class")
        
        for i, elem in enumerate(card_like[:3]):
            print(f"Card-like {i+1}: {elem.name} class='{elem.get('class')}'")
        
        # Look for RESULTS links
        results_links = soup.find_all('a', string='RESULTS')
        print(f"Found {len(results_links)} RESULTS links")
        
        for i, link in enumerate(results_links[:3]):
            print(f"RESULTS link {i+1}: {link.get('href')}")
        
        # Look for any h5 elements
        h5_elements = soup.find_all('h5')
        print(f"Found {len(h5_elements)} h5 elements")
        
        for i, h5 in enumerate(h5_elements[:3]):
            print(f"H5 {i+1}: {h5.get_text(strip=True)[:50]}...")
        
        await browser.close()

asyncio.run(main())
#!/usr/bin/env ./venv/bin/python3
"""
Debug script to investigate Music League page structure
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

class PageDebugger:
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

    async def debug_completed_page(self):
        """Debug the completed leagues page structure"""
        print("="*70)
        print("DEBUGGING COMPLETED LEAGUES PAGE")
        print("="*70)
        
        # Navigate to completed page
        print(f"Navigating to {ML_COMPLETED_URL}...")
        await self.page.goto(ML_COMPLETED_URL, wait_until='domcontentloaded')
        
        # Wait for initial load
        print("Waiting for initial load...")
        await asyncio.sleep(3)
        
        # Check various load states
        print(f"Current URL: {self.page.url}")
        print(f"Page title: {await self.page.title()}")
        
        # Check for different types of content over time
        for i in range(6):  # Check 6 times over 30 seconds
            print(f"\n--- Check {i+1} (after {i*5} seconds) ---")
            
            # Get basic page info
            content = await self.page.content()
            print(f"Page content length: {len(content)} characters")
            
            # Check for "Bard's Tale"
            bards_tale_count = content.count("Bard's Tale")
            print(f"'Bard's Tale' occurrences: {bards_tale_count}")
            
            # Check for various selectors
            selectors_to_check = [
                '.league-tile',
                '.league-card', 
                '.league-item',
                '[data-testid*="league"]',
                'a[href*="/l/"]',
                '[href*="/l/"]',
                'div[class*="league"]',
                'div[class*="card"]',
                'div[class*="tile"]',
                'div[class*="item"]'
            ]
            
            for selector in selectors_to_check:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        print(f"  {selector}: {len(elements)} elements")
                        # Get first element's outer HTML
                        if elements:
                            first_element = elements[0]
                            outer_html = await first_element.evaluate('el => el.outerHTML')
                            print(f"    First element HTML (truncated): {outer_html[:100]}...")
                except Exception as e:
                    pass
            
            # Look for any links with /l/ pattern
            try:
                league_links = await self.page.query_selector_all('a[href*="/l/"]')
                print(f"  League links found: {len(league_links)}")
                for i, link in enumerate(league_links[:3]):  # Show first 3
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    print(f"    Link {i+1}: {href} - '{text[:50]}...'")
            except:
                pass
            
            # Check for dynamic content indicators
            try:
                script_tags = await self.page.query_selector_all('script')
                print(f"  Script tags: {len(script_tags)}")
                
                # Look for React/Vue/Angular indicators
                if 'react' in content.lower():
                    print("  React detected in page")
                if 'vue' in content.lower():
                    print("  Vue detected in page")
                if 'angular' in content.lower():
                    print("  Angular detected in page")
                    
            except:
                pass
            
            # Scroll a bit to trigger loading
            if i < 5:
                print("  Scrolling to trigger dynamic loading...")
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(5)
        
        # Final comprehensive scan
        print("\n" + "="*50)
        print("FINAL COMPREHENSIVE SCAN")
        print("="*50)
        
        # Wait for network to be idle
        try:
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            print("Network idle state reached")
        except:
            print("Network idle timeout")
        
        # Get final page content
        final_content = await self.page.content()
        soup = BeautifulSoup(final_content, 'html.parser')
        
        # Look for all links
        all_links = soup.find_all('a', href=True)
        league_links = [link for link in all_links if '/l/' in link.get('href', '')]
        
        print(f"Total links on page: {len(all_links)}")
        print(f"League links (/l/ pattern): {len(league_links)}")
        
        # Extract unique league IDs
        league_ids = set()
        for link in league_links:
            href = link.get('href', '')
            match = re.search(r'/l/([a-f0-9]{32})', href)
            if match:
                league_ids.add(match.group(1))
        
        print(f"Unique league IDs found: {len(league_ids)}")
        
        # Look for Bard's Tale specifically
        bards_tale_links = []
        for link in league_links:
            link_text = link.get_text(strip=True)
            if "Bard's Tale" in link_text:
                bards_tale_links.append({
                    'text': link_text,
                    'href': link.get('href'),
                    'html': str(link)[:200]
                })
        
        print(f"Bard's Tale specific links: {len(bards_tale_links)}")
        for i, link in enumerate(bards_tale_links[:5]):  # Show first 5
            print(f"  {i+1}. {link['text']} -> {link['href']}")
        
        # Save debug output
        debug_file = DATA_DIR / "debug_page_content.html"
        with open(debug_file, 'w') as f:
            f.write(final_content)
        print(f"\nFull page HTML saved to: {debug_file}")
        
        return {
            'league_links': len(league_links),
            'league_ids': list(league_ids),
            'bards_tale_links': bards_tale_links
        }

    async def test_league_page(self, league_id):
        """Test loading a specific league page"""
        print(f"\n" + "="*70)
        print(f"TESTING BARD'S TALE 26 LEAGUE PAGE: {league_id}")
        print("="*70)
        
        league_url = f"{ML_BASE_URL}/l/{league_id}/"
        print(f"Navigating to: {league_url}")
        
        try:
            await self.page.goto(league_url, wait_until='domcontentloaded')
            await asyncio.sleep(5)  # Wait longer for content to load
            
            content = await self.page.content()
            print(f"League page content length: {len(content)}")
            print(f"Current URL: {self.page.url}")
            print(f"Page title: {await self.page.title()}")
            
            # Look for rounds/songs structure
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for round links and their context
            print("\nSearching for round links and context:")
            
            round_pattern = r'/l/' + league_id + r'/[a-f0-9]{32}'
            round_links = soup.find_all('a', href=re.compile(round_pattern))
            print(f"Found {len(round_links)} round links")
            
            for j, link in enumerate(round_links):
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                
                print(f"\n--- Round Link {j+1} ---")
                print(f"Link text: '{link_text}'")
                print(f"URL: {href}")
                
                # Find parent container and extract surrounding text
                parent = link.find_parent()
                level = 0
                while parent and level < 5:  # Go up max 5 levels
                    parent_text = parent.get_text(strip=True)
                    if parent_text and len(parent_text) > 20:  # Only show substantial content
                        print(f"Parent {level}: '{parent_text[:200]}...'")
                        
                        # Look for round number, title, and description patterns
                        lines = [line.strip() for line in parent_text.split('\n') if line.strip()]
                        potential_round_info = []
                        for line in lines:
                            if any(pattern in line.upper() for pattern in ['ROUND', 'B26.', '70S', 'OBVIOUSLY']):
                                potential_round_info.append(line)
                        
                        if potential_round_info:
                            print(f"  Potential round info: {potential_round_info}")
                        break
                    parent = parent.find_parent()
                    level += 1
                
                # Also check siblings
                siblings = link.find_parent().find_all(['div', 'span', 'h1', 'h2', 'h3', 'h4', 'p'])
                for sibling in siblings[:10]:  # Check first 10 siblings
                    sibling_text = sibling.get_text(strip=True)
                    if sibling_text and any(pattern in sibling_text.upper() for pattern in ['ROUND', 'B26.', '70S', 'OBVIOUSLY']):
                        print(f"  Sibling info: '{sibling_text}'")
                        break
            
            # Look for round-related elements with different selectors
            print("\nSearching for round elements with different selectors:")
            
            round_selectors = [
                '.round',
                '.round-tile', 
                '.round-card',
                '.round-item',
                '[class*="round"]',
                '[data-testid*="round"]',
                'div:contains("Round")',
                'div:contains("RESULTS")'
            ]
            
            for selector in round_selectors:
                try:
                    if 'contains' in selector:
                        # Handle CSS :contains() which BeautifulSoup doesn't support
                        elements = soup.find_all('div', string=re.compile(r'Round|RESULTS', re.I))
                    else:
                        elements = soup.select(selector)
                    
                    if elements:
                        print(f"  {selector}: {len(elements)} elements")
                        for j, elem in enumerate(elements[:3]):
                            text = elem.get_text(strip=True)[:50]
                            print(f"    {j+1}. '{text}...'")
                except Exception as e:
                    print(f"  {selector}: Error - {e}")
            
            # Look for any text mentioning rounds
            print(f"\nText analysis:")
            print(f"'Round' occurrences: {content.count('Round')}")
            print(f"'RESULTS' occurrences: {content.count('RESULTS')}")
            print(f"'round' occurrences: {content.count('round')}")
            
            # Save the league page HTML for manual inspection
            debug_file = Path("data") / f"debug_league_{league_id}.html"
            with open(debug_file, 'w') as f:
                f.write(content)
            print(f"\nLeague page HTML saved to: {debug_file}")
            
        except Exception as e:
            print(f"Error loading league page: {e}")

    async def cleanup(self):
        if self.browser:
            await self.browser.close()

async def main():
    debugger = PageDebugger()
    
    try:
        await debugger.setup_browser()
        
        # Debug the completed page
        results = await debugger.debug_completed_page()
        
        # Test Bard's Tale 26 specifically  
        bards_tale_26_id = "85191779017d4150b28cc5a67946d57c"
        await debugger.test_league_page(bards_tale_26_id)
        
        print("\n" + "="*70)
        print("DEBUG COMPLETE")
        print("="*70)
        print("Check the saved HTML file for detailed analysis")
        
    except Exception as e:
        logger.error(f"Debug error: {e}")
    finally:
        await debugger.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
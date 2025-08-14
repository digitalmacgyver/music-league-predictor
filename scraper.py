#!/usr/bin/env ./venv/bin/python3
"""
Music League Web Scraper with Spotify SSO Authentication

Usage:
    ./scraper.py [update|clean|match <pattern>]
    
    update  - Default mode: process leagues not in database (incremental)
    clean   - Full refresh: backup database and rescan all leagues
    match   - Process only leagues containing pattern (case-insensitive)
"""

import argparse
import asyncio
import json
import logging
import random
import re
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from config import *
from setup_db import get_db_connection

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MusicLeagueScraper:
    """Main scraper class for Music League data extraction"""
    
    def __init__(self, mode: str = "update", match_pattern: str = None):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_data: Dict = {}
        self.is_authenticated = False
        self.mode = mode
        self.match_pattern = match_pattern
        
        # Load existing leagues for update mode
        self.existing_league_ids = set()
        if mode == "update" and DATABASE_PATH.exists():
            self._load_existing_leagues()
    
    def _load_existing_leagues(self):
        """Load existing league IDs from database for update mode"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM leagues")
            self.existing_league_ids = {row[0] for row in cursor.fetchall()}
            logger.info(f"Found {len(self.existing_league_ids)} existing leagues in database")
            conn.close()
        except Exception as e:
            logger.warning(f"Could not load existing leagues: {e}")
        
    async def initialize(self):
        """Initialize the browser and context"""
        playwright = await async_playwright().start()
        
        # Launch browser with appropriate settings
        self.browser = await playwright.chromium.launch(
            headless=HEADLESS_MODE,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        # Create context with saved session if available
        context_options = {
            "viewport": VIEWPORT,
            "user_agent": USER_AGENT,
            "ignore_https_errors": True,
        }
        
        # Load saved session if exists
        if SESSION_PATH.exists():
            try:
                with open(SESSION_PATH, 'r') as f:
                    session_data = json.load(f)
                    if 'cookies' in session_data:
                        context_options['storage_state'] = session_data
                        logger.info("Loaded saved session data")
            except Exception as e:
                logger.warning(f"Could not load session: {e}")
        
        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()
        
        # Set default timeouts
        self.page.set_default_timeout(PAGE_LOAD_TIMEOUT)
        
    async def load_session(self):
        """Load saved session state"""
        try:
            if not SESSION_PATH.exists():
                logger.error("No session file found. Please run ./login.py first to authenticate.")
                return False
                
            with open(SESSION_PATH, 'r') as f:
                session_data = json.load(f)
                if 'cookies' in session_data and session_data['cookies']:
                    await self.context.add_cookies(session_data['cookies'])
                    logger.info("Loaded saved session cookies")
                    return True
                else:
                    logger.error("Session file exists but contains no cookies. Please run ./login.py")
                    return False
        except Exception as e:
            logger.error(f"Could not load session: {e}")
            logger.error("Please run ./login.py to authenticate first.")
            return False
    
    async def verify_authentication(self):
        """Simple verification that we can access the completed leagues page"""
        try:
            await self.page.goto(ML_COMPLETED_URL, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)
            
            current_url = self.page.url
            page_content = await self.page.content()
            
            # Check if redirected to login
            if any(path in current_url for path in ['/login', '/authorize', 'accounts.spotify.com']):
                logger.error("Redirected to login page - session expired")
                return False
            
            # Check for basic content
            if '/completed' in current_url and len(page_content) > 1000:
                logger.info("Successfully accessed completed leagues page")
                self.is_authenticated = True
                return True
            
            logger.error("Could not access completed leagues page properly")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying authentication: {e}")
            return False
    
    async def scroll_to_load_all(self, selector: str = None, max_scrolls: int = 50) -> int:
        """Scroll page to load all dynamic content"""
        previous_height = 0
        scrolls = 0
        items_count = 0
        
        while scrolls < max_scrolls:
            # Get current scroll height
            current_height = await self.page.evaluate('document.body.scrollHeight')
            
            # Count items if selector provided
            if selector:
                items = await self.page.query_selector_all(selector)
                items_count = len(items)
                logger.debug(f"Found {items_count} items after {scrolls} scrolls")
            
            # Scroll to bottom
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            
            # Wait for new content to load
            await asyncio.sleep(SCROLL_PAUSE_TIME)
            
            # Check if new content was loaded
            if current_height == previous_height:
                logger.debug("No new content loaded, stopping scroll")
                break
            
            previous_height = current_height
            scrolls += 1
        
        return items_count
    
    async def ensure_comments_visible(self):
        """Ensure comments are visible by clicking show comments button if needed"""
        try:
            # Look for "Show comments" button and click it
            show_button = await self.page.query_selector("button:has-text('Show comments')")
            if show_button:
                logger.debug("Clicking 'Show comments' button")
                await show_button.click()
                await asyncio.sleep(2)  # Wait for dynamic content to load
            else:
                logger.debug("Comments already visible or no toggle found")
        except Exception as e:
            logger.debug(f"Error ensuring comments visible: {e}")
    
    async def get_leagues(self) -> List[Dict]:
        """Get all completed leagues"""
        logger.info("Fetching completed leagues...")
        
        await self.page.goto(ML_COMPLETED_URL, wait_until='domcontentloaded')
        await asyncio.sleep(3)  # Initial wait
        
        # Scroll to load all leagues progressively
        await self.scroll_to_load_all('.league-tile')
        
        # Wait for network idle after scrolling
        try:
            await self.page.wait_for_load_state('networkidle', timeout=10000)
        except:
            pass
        
        # Get page content
        content = await self.page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        leagues = []
        
        # Find all links with league URLs directly
        league_links = soup.find_all('a', href=re.compile(r'/l/[a-f0-9]{32}/'))
        
        logger.info(f"Found {len(league_links)} total league links")
        
        processed_ids = set()  # Track unique league IDs
        
        for link in league_links:
            try:
                href = link.get('href', '')
                
                # Extract league ID from URL
                league_id_match = re.search(r'/l/([a-f0-9]{32})/', href)
                if not league_id_match:
                    continue
                    
                league_id = league_id_match.group(1)
                
                # Skip if we've already processed this league
                if league_id in processed_ids:
                    continue
                    
                # Get league title from link text
                title = link.get_text(strip=True)
                
                # Skip empty titles or create league links
                if not title or 'create' in title.lower():
                    continue
                
                league_url = f"{ML_BASE_URL}/l/{league_id}/"
                
                # Apply filtering based on mode
                should_include = False
                
                if self.mode == "match" and self.match_pattern:
                    # Match mode: only include leagues containing the pattern
                    should_include = self.match_pattern.lower() in title.lower()
                elif self.mode == "update":
                    # Update mode: only include leagues not in database
                    if league_id not in self.existing_league_ids:
                        # Apply existing filters for new leagues
                        if SCRAPE_ALL_LEAGUES:
                            should_include = True
                        else:
                            # Check for various Bard's Tale patterns
                            title_lower = title.lower()
                            # Also check the exact unicode string
                            if (LEAGUE_FILTER.lower() in title_lower or 
                                "bardalon" in title_lower or
                                title == "Bard's Tale" or  # Exact match with unicode apostrophe
                                title_lower == "bard's tale"):  # Lowercase match
                                should_include = True
                elif self.mode == "clean":
                    # Clean mode: process all leagues matching original criteria
                    if SCRAPE_ALL_LEAGUES:
                        should_include = True
                    else:
                        # Check for various Bard's Tale patterns
                        title_lower = title.lower()
                        if (LEAGUE_FILTER.lower() in title_lower or 
                            "bardalon" in title_lower or
                            title == "Bard's Tale" or  # Exact match with unicode apostrophe
                            title_lower == "bard's tale"):  # Lowercase match
                            should_include = True
                
                # Test mode override - only process specific league
                if TEST_MODE and TEST_LEAGUE:
                    should_include = (TEST_LEAGUE.lower() in title.lower())
                
                if should_include:
                    leagues.append({
                        'id': league_id,
                        'title': title,
                        'url': league_url
                    })
                    processed_ids.add(league_id)
                    logger.info(f"Found league: {title}")
                    
            except Exception as e:
                logger.warning(f"Error parsing league link: {e}")
                continue
        
        mode_info = f"{self.mode} mode"
        if self.mode == "match":
            mode_info += f" (pattern: '{self.match_pattern}')"
        elif self.mode == "update":
            mode_info += f" (skipped {len(processed_ids) - len(leagues)} existing leagues)"
        logger.info(f"Found {len(leagues)} leagues for {mode_info}")
        return leagues
    
    async def get_league_rounds(self, league_id: str, league_url: str) -> List[Dict]:
        """Get all rounds for a specific league"""
        logger.info(f"Fetching rounds for league {league_id}")
        
        await self.page.goto(league_url, wait_until='domcontentloaded')
        await asyncio.sleep(3)  # Wait for page to load
        
        content = await self.page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        # Debug: check if page has content
        if len(content) < 1000:  # Very basic content check
            logger.warning(f"Page seems incomplete, content length: {len(content)}")
            logger.debug(f"First 200 chars: {content[:200]}")
            # Save the problematic content for debugging
            debug_file = f"data/debug_empty_league_{league_id}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.debug(f"Saved incomplete page content to {debug_file}")
            return []
        
        rounds = []
        
        # Debug: save the content when we do get it
        debug_file = f"data/debug_league_content_{league_id}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Saved full page content to {debug_file}")
        
        # Find all round cards based on the HTML structure
        # Round cards have class="card" and contain round information
        round_cards = soup.find_all('div', class_='card')
        
        logger.info(f"Found {len(round_cards)} potential round cards")
        
        processed_round_ids = set()
        
        for card in round_cards:
            try:
                # Find the RESULTS link within this card
                round_pattern = f'/l/{league_id}/([a-f0-9]{{32}})/'
                # Look for a link with the pattern that contains "RESULTS" text (in a child element)
                results_link = card.find('a', href=re.compile(round_pattern))
                if results_link:
                    # Check if this link contains "RESULTS" text anywhere within it
                    if not results_link.find(string='RESULTS'):
                        results_link = None
                
                if not results_link:
                    continue
                
                href = results_link.get('href', '')
                round_id_match = re.search(round_pattern, href)
                if not round_id_match:
                    continue
                
                round_id = round_id_match.group(1)
                
                # Skip if we've already processed this round
                if round_id in processed_round_ids:
                    continue
                
                # Extract round title from h5.card-title
                title = f"Round {len(rounds) + 1}"  # Default
                round_number = len(rounds) + 1
                
                card_title = card.find('h5', class_='card-title')
                if card_title:
                    title_text = card_title.get_text(strip=True)
                    # Parse round number and title from text like "B26.1 Separating the Art from the Dirtbag Artist"
                    # or "ROUND 1B1.1 Earworms"
                    
                    # Try to extract round number
                    round_num_match = re.search(r'ROUND\s*(\d+)', title_text, re.IGNORECASE)
                    if round_num_match:
                        round_number = int(round_num_match.group(1))
                        # Remove "ROUND N" prefix from title
                        title = re.sub(r'^ROUND\s*\d+\s*', '', title_text, flags=re.IGNORECASE).strip()
                    else:
                        # Look for patterns like "B26.1" or "1B1.1" at the beginning
                        prefix_match = re.match(r'^[A-Z]*\d+\.\d+\s+(.+)', title_text)
                        if prefix_match:
                            title = prefix_match.group(1).strip()
                            # Extract numeric part for round number
                            num_match = re.search(r'\.(\d+)', title_text)
                            if num_match:
                                round_number = int(num_match.group(1))
                        else:
                            title = title_text
                
                # Extract round description from p.card-text with x-html attribute
                description = ""
                x_html_elem = card.find(attrs={'x-html': True})
                if x_html_elem:
                    # The x-html contains the linkifyStr processed description
                    # Get the parent p.card-text element
                    card_text = x_html_elem.find_parent('p', class_='card-text')
                    if not card_text:
                        card_text = x_html_elem if x_html_elem.name == 'p' else None
                    
                    if card_text:
                        # Get text content, preserving line breaks
                        # Use .strings generator to preserve structure
                        desc_parts = []
                        for string in card_text.strings:
                            desc_parts.append(string)
                        description = ''.join(desc_parts).strip()
                
                # If no x-html, try regular card-text
                if not description:
                    card_text = card.find('p', class_='card-text')
                    if card_text:
                        # Preserve newlines by getting text with separator
                        description = card_text.get_text(separator='\n', strip=True)
                
                round_url = f"{ML_BASE_URL}/l/{league_id}/{round_id}/"
                
                rounds.append({
                    'id': round_id,
                    'league_id': league_id,
                    'round_number': round_number,
                    'title': title,
                    'description': description,
                    'url': round_url
                })
                
                processed_round_ids.add(round_id)
                logger.info(f"Found round {round_number}: '{title}' -> {round_url}")
                
            except Exception as e:
                logger.warning(f"Error parsing round card: {e}")
                continue
        
        logger.info(f"Found {len(rounds)} rounds total")
        return rounds
    
    async def get_round_songs(self, round_url: str, round_id: str, league_id: str) -> List[Dict]:
        """Get all songs and votes for a specific round"""
        logger.info(f"Fetching songs for round {round_id}")
        
        await self.page.goto(round_url, wait_until='networkidle')
        await asyncio.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
        
        # Ensure comments are visible for vote parsing
        await self.ensure_comments_visible()
        
        # Scroll to load all songs
        await self.scroll_to_load_all('.song-card, [data-testid="song-card"]')
        
        content = await self.page.content()
        soup = BeautifulSoup(content, 'lxml')
        
        songs = []
        
        # Find song cards - based on debug findings, songs are in cards with voting info
        song_cards = soup.find_all('div', class_='card')
        
        logger.info(f"Found {len(song_cards)} potential song cards")
        
        for order, card in enumerate(song_cards, 1):
            try:
                song_data = self.parse_song_card(card, round_id, league_id, order)
                if song_data:
                    songs.append(song_data)
                    logger.info(f"Found song: '{song_data['title']}' by {song_data['artist']} ({song_data['final_score']} final score)")
            except Exception as e:
                logger.warning(f"Error parsing song card: {e}")
                continue
        
        logger.info(f"Found {len(songs)} songs total")
        return songs
    
    def parse_song_card(self, card, round_id: str, league_id: str, order: int) -> Optional[Dict]:
        """Parse a song card to extract all data based on actual HTML structure"""
        try:
            # Check if this card contains a song (has Spotify link and vote info)
            spotify_link = card.find('a', href=re.compile('spotify.com/track'))
            vote_info = card.find('p', string=re.compile(r'\d+\s+voters?'))
            
            if not (spotify_link and vote_info):
                return None  # Not a song card
            
            # Extract song title from Spotify link
            title = spotify_link.get_text(strip=True)
            spotify_url = spotify_link.get('href')
            
            # Extract artist and album from card-text elements
            card_texts = card.find_all('p', class_='card-text')
            artist = ""
            album = ""
            
            for i, text_elem in enumerate(card_texts):
                text = text_elem.get_text(strip=True)
                # Skip elements with icons or "from Spotify"
                if 'spotify' in text.lower() or not text:
                    continue
                
                # First card-text is usually artist, second is album
                if not artist and 'text-body-secondary' not in text_elem.get('class', []):
                    artist = text
                elif not album and 'text-body-secondary' in text_elem.get('class', []):
                    album = text
            
            # We'll calculate total_votes from individual votes later
            # The h3 element contains ranking or other data, not vote totals
            total_votes = 0
            
            # Extract number of voters
            voters_match = re.search(r'(\d+)\s+voters?', vote_info.get_text())
            num_voters = int(voters_match.group(1)) if voters_match else 0
            
            # Extract submitter name from ranking section
            submitter = "Unknown"
            ranking_section = card.find('div', class_=re.compile(r'rank-\d+'))
            if ranking_section:
                submitter_row = ranking_section.find('div', class_='row')
                if submitter_row:
                    submitter_div = submitter_row.find('div', class_=['col', 'text-truncate'])
                    if submitter_div:
                        full_text = submitter_div.get_text(separator='|', strip=True)
                        
                        if '|' in full_text:
                            parts = full_text.split('|', 1)
                            submitter = parts[0].strip()
                        else:
                            words = full_text.split()
                            if len(words) > 3:
                                submitter = ' '.join(words[:2])
                            else:
                                submitter = full_text
                        
                        submitter = re.sub(r'Did not vote.*$', '', submitter).strip()
                        submitter = re.sub(r'\s+', ' ', submitter).strip()
                        
                        if not submitter or len(submitter) < 2:
                            submitter = "Unknown"
            
            # Extract submitter comment from dedicated card-body section
            submitter_comment = ""
            comment_containers = card.find_all(['div', 'p'], class_=['card-body', 'bg-body-tertiary'])
            for container in comment_containers:
                text = container.get_text(strip=True)
                # Look for substantial text that appears to be a comment (not metadata)
                if (len(text) > 50 and 
                    not any(skip in text.lower() for skip in ['spotify', 'voter', 'from', 'track'])):
                    submitter_comment = text
                    break
            
            # Parse individual votes from card-footer DOM structure
            votes = []
            card_footer = card.find('div', class_='card-footer')
            if card_footer and 'show' in card_footer.get('class', []):
                votes = self.parse_footer_votes(card_footer)
            
            # Calculate total_votes_awarded by summing individual vote points
            total_votes_awarded = sum(vote['points'] for vote in votes)
            
            # Detect rule violations and extract final_score
            final_score = total_votes_awarded  # Default to same as awarded votes
            
            # Look for rule violation pattern: <s class="text-danger">awarded_votes</s>final_score
            strike_elem = card.find('s', class_='text-danger')
            if strike_elem:
                # This indicates a rule violation - the final score should be different
                strike_text = strike_elem.get_text(strip=True)
                if strike_text.isdigit():
                    # The struck-through number should match our calculated total
                    struck_votes = int(strike_text)
                    logger.debug(f"Found rule violation: awarded {struck_votes}, calculated {total_votes_awarded}")
                    
                    # Look for the final score immediately after the </s> tag
                    parent = strike_elem.parent
                    if parent:
                        parent_text = parent.get_text()
                        # Find text after the struck-through portion
                        strike_end_pos = parent_text.find(strike_text) + len(strike_text)
                        remaining_text = parent_text[strike_end_pos:].strip()
                        
                        # Extract the final score (should be a number, likely 0)
                        final_score_match = re.search(r'(\d+)', remaining_text)
                        if final_score_match:
                            final_score = int(final_score_match.group(1))
                            logger.info(f"Rule violation detected: '{title}' awarded {total_votes_awarded} votes, final score {final_score}")
            
            # Return song data
            return {
                'round_id': round_id,
                'league_id': league_id,
                'title': title,
                'artist': artist,
                'album': album,
                'submitter': submitter,
                'submitter_comment': submitter_comment,
                'total_votes_awarded': total_votes_awarded,
                'final_score': final_score,
                'num_voters': num_voters,
                'spotify_url': spotify_url,
                'song_order': order,
                'votes': votes
            }
            
        except Exception as e:
            logger.debug(f"Error parsing song card: {e}")
            return None
    
    def parse_vote_element(self, element) -> Optional[Dict]:
        """Parse a vote element to extract voter data"""
        try:
            voter_elem = element.find(['span', 'div'], class_=re.compile('voter|user|name'))
            points_elem = element.find(['span', 'div'], class_=re.compile('point|score|vote'))
            comment_elem = element.find(['p', 'div'], class_=re.compile('comment|text'))
            
            if not voter_elem:
                return None
            
            voter = voter_elem.get_text(strip=True)
            
            # Extract points (0-5)
            points = 0
            if points_elem:
                points_text = points_elem.get_text(strip=True)
                points_match = re.search(r'(\d+)', points_text)
                if points_match:
                    points = min(5, max(0, int(points_match.group(1))))
            
            comment = comment_elem.get_text(strip=True) if comment_elem else ""
            
            return {
                'voter': voter,
                'points': points,
                'comment': comment
            }
            
        except Exception as e:
            logger.error(f"Error parsing vote: {e}")
            return None
    
    def parse_footer_votes(self, card_footer) -> List[Dict]:
        """Parse vote data directly from card-footer DOM structure"""
        votes = []
        if not card_footer:
            return votes
            
        try:
            # Find all vote containers (each vote is in a row)
            vote_rows = card_footer.find_all('div', class_='row align-items-start gx-3 my-3')
            
            for row in vote_rows:
                # Extract voter name from <b> tag
                voter_tag = row.find('b', class_='d-block text-truncate text-body')
                if not voter_tag:
                    continue
                    
                voter_name = voter_tag.get_text(strip=True)
                
                # Extract comment from <span> tag with text-break class
                comment_tag = row.find('span', class_='text-break ws-pre-wrap')
                comment = comment_tag.get_text(strip=True) if comment_tag else ""
                
                # Extract points from <h6> tag
                points_tag = row.find('h6', class_='m-0')
                if not points_tag:
                    continue
                    
                points_text = points_tag.get_text(strip=True)
                try:
                    points = int(points_text)
                except ValueError:
                    continue
                
                votes.append({
                    'voter': voter_name,
                    'points': points,
                    'comment': comment
                })
                    
        except Exception as e:
            logger.debug(f"Error parsing footer votes: {e}")
            
        return votes
    
    def is_valid_voter_name(self, name: str) -> bool:
        """Check if a string looks like a legitimate voter name"""
        if not name or len(name) > 30:
            return False
            
        # Skip obvious non-names
        invalid_patterns = [
            r'http[s]?://',  # URLs
            r'www\.',        # URLs
            r'\.com',        # URLs
            r'[.]{3,}',      # Multiple dots (ellipsis)
            r'^[^a-zA-Z]',   # Doesn't start with letter
            r'[?!]{2,}',     # Multiple punctuation
            r'^\d+$',        # Just numbers
            r'^["\']{1}',    # Starts with quote
            r'[()]{2,}',     # Multiple parentheses
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name):
                return False
        
        # Skip very long sentences or comments
        if len(name.split()) > 6:  # More than 6 words is likely a comment
            return False
            
        # Skip common comment phrases
        comment_phrases = [
            'this is', 'i love', 'great song', 'this song', 'amazing',
            'awesome', 'perfect', 'incredible', 'beautiful', 'brilliant',
            'fantastic', 'wonderful', 'excellent', 'outstanding', 'superb',
            'and she wrote', 'we also would', 'one of my', 'hard to',
            'i freaking', 'use your', 'walked around', 'drove by'
        ]
        
        name_lower = name.lower()
        for phrase in comment_phrases:
            if phrase in name_lower:
                return False
                
        return True
    
    def save_to_database(self, data_type: str, data: List[Dict]):
        """Save scraped data to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if data_type == 'leagues':
                for league in data:
                    cursor.execute("""
                        INSERT OR REPLACE INTO leagues (id, title, url)
                        VALUES (?, ?, ?)
                    """, (league['id'], league['title'], league['url']))
                    
                    # Update progress
                    cursor.execute("""
                        INSERT OR REPLACE INTO scraping_progress (entity_type, entity_id, status)
                        VALUES ('league', ?, 'completed')
                    """, (league['id'],))
            
            elif data_type == 'rounds':
                for round_data in data:
                    cursor.execute("""
                        INSERT OR REPLACE INTO rounds 
                        (id, league_id, round_number, title, description, url)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        round_data['id'],
                        round_data['league_id'],
                        round_data['round_number'],
                        round_data['title'],
                        round_data['description'],
                        round_data['url']
                    ))
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO scraping_progress (entity_type, entity_id, status)
                        VALUES ('round', ?, 'completed')
                    """, (round_data['id'],))
            
            elif data_type == 'songs':
                for song in data:
                    # Insert song
                    cursor.execute("""
                        INSERT OR REPLACE INTO songs 
                        (round_id, league_id, title, artist, album, spotify_url, 
                         submitter, submitter_comment, total_votes_awarded, final_score, num_voters, song_order)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        song['round_id'],
                        song['league_id'],
                        song['title'],
                        song['artist'],
                        song['album'],
                        song['spotify_url'],
                        song['submitter'],
                        song['submitter_comment'],
                        song['total_votes_awarded'],
                        song['final_score'],
                        song['num_voters'],
                        song['song_order']
                    ))
                    
                    song_id = cursor.lastrowid
                    
                    # Insert votes
                    for vote in song.get('votes', []):
                        cursor.execute("""
                            INSERT OR REPLACE INTO votes 
                            (song_id, round_id, league_id, voter, points, comment)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            song_id,
                            song['round_id'],
                            song['league_id'],
                            vote['voter'],
                            vote['points'],
                            vote['comment']
                        ))
            
            conn.commit()
            logger.info(f"Saved {len(data)} {data_type} to database")
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    async def scrape_all(self):
        """Main scraping orchestration"""
        try:
            # Initialize browser
            await self.initialize()
            
            # Load session and verify authentication
            if not await self.load_session():
                print("\n" + "="*60)
                print("NO VALID SESSION FOUND")
                print("="*60)
                print("Please run ./login.py first to authenticate with Music League")
                print("="*60 + "\n")
                return
            
            if not await self.verify_authentication():
                print("\n" + "="*60)
                print("SESSION EXPIRED")
                print("="*60)
                print("Your session has expired. Please run ./login.py to re-authenticate")
                print("="*60 + "\n")
                return
            
            # Get all leagues
            leagues = await self.get_leagues()
            self.save_to_database('leagues', leagues)
            
            # Process each league
            for league in tqdm(leagues, desc="Processing leagues"):
                logger.info(f"Processing league: {league['title']}")
                
                try:
                    # Get rounds for this league
                    rounds = await self.get_league_rounds(league['id'], league['url'])
                    self.save_to_database('rounds', rounds)
                    
                    # Process each round
                    for round_data in tqdm(rounds, desc=f"Processing rounds for {league['title']}", leave=False):
                        logger.info(f"Processing round: {round_data['title']}")
                        
                        try:
                            # Get songs for this round
                            songs = await self.get_round_songs(
                                round_data['url'],
                                round_data['id'],
                                league['id']
                            )
                            self.save_to_database('songs', songs)
                            
                            # Rate limiting
                            await asyncio.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
                            
                        except Exception as e:
                            logger.error(f"Error processing round {round_data['id']}: {e}")
                            continue
                    
                except Exception as e:
                    logger.error(f"Error processing league {league['id']}: {e}")
                    continue
            
            logger.info("Scraping completed successfully!")
            
        except Exception as e:
            logger.error(f"Fatal error during scraping: {e}")
            raise
        finally:
            # Clean up
            if self.browser:
                await self.browser.close()


def backup_database():
    """Create a backup of the database before clean mode"""
    if not DATABASE_PATH.exists():
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DATABASE_PATH.parent / f"music_league_backup_{timestamp}.db"
    
    try:
        shutil.copy2(DATABASE_PATH, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        print(f"❌ Failed to backup database: {e}")
        return None


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Music League Web Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  update    Default mode. Process only leagues not in database (incremental)
  clean     Full refresh. Backup database and rescan all leagues
  match     Process only leagues containing pattern (case-insensitive)

Examples:
  ./scraper.py                    # Update mode (default)
  ./scraper.py update             # Same as above
  ./scraper.py clean              # Full refresh with backup
  ./scraper.py match "bard"       # Only leagues containing "bard"
  ./scraper.py match "Tale 25"    # Only leagues containing "Tale 25"
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Update mode (default)
    update_parser = subparsers.add_parser('update', help='Incremental update (default)')
    
    # Clean mode  
    clean_parser = subparsers.add_parser('clean', help='Full refresh with backup')
    
    # Match mode
    match_parser = subparsers.add_parser('match', help='Process leagues matching pattern')
    match_parser.add_argument('pattern', help='Pattern to match in league names')
    
    args = parser.parse_args()
    
    # Default to update if no mode specified
    if args.mode is None:
        args.mode = 'update'
        args.pattern = None
    elif args.mode == 'match' and not hasattr(args, 'pattern'):
        parser.error("match mode requires a pattern argument")
    else:
        args.pattern = getattr(args, 'pattern', None)
    
    return args


async def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    print("\n" + "="*60)
    print("MUSIC LEAGUE SCRAPER")
    print("="*60)
    print(f"Mode: {args.mode.upper()}")
    if args.mode == "match":
        print(f"Pattern: '{args.pattern}'")
    print(f"Database: {DATABASE_PATH}")
    print(f"Session: {SESSION_PATH}")
    if args.mode != "match":
        print(f"Filter: {LEAGUE_FILTER if not SCRAPE_ALL_LEAGUES else 'All leagues'}")
    print("="*60 + "\n")
    
    # Handle clean mode - backup database first, then recreate
    if args.mode == "clean":
        if DATABASE_PATH.exists():
            backup_path = backup_database()
            if backup_path is None:
                print("❌ Cannot proceed without successful backup in clean mode")
                return
            # Remove old database for clean mode
            DATABASE_PATH.unlink()
            print("🗑️  Removed old database for clean rebuild")
        
        # Create fresh database for clean mode
        print("Creating fresh database...")
        from setup_db import create_database
        create_database()
    else:
        # Create database if it doesn't exist (for update/match modes)
        if not DATABASE_PATH.exists():
            print("Creating database...")
            from setup_db import create_database
            create_database()
    
    # Run scraper with specified mode
    scraper = MusicLeagueScraper(mode=args.mode, match_pattern=args.pattern)
    await scraper.scrape_all()
    
    print("\n" + "="*60)
    print("SCRAPING COMPLETE")
    print("="*60)
    print(f"Mode: {args.mode.upper()}")
    print(f"Data saved to: {DATABASE_PATH}")
    print("Run 'python reports.py' to generate reports")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
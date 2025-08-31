#!/usr/bin/env ./venv/bin/python3
"""
Lyrics Analysis for Music League Theme Matching

Fetches song lyrics from multiple sources and performs LLM-based analysis
to determine how well lyrics match a given theme.
"""

import os
import time
import logging
import re
import json
import hashlib
import sqlite3
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
from dotenv import load_dotenv

from music_league.setup_db import get_db_connection
from music_league.cached_llm_client import CachedAnthropicClient

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class LyricsResult:
    """Result from lyrics fetching"""
    lyrics: str
    source: str
    confidence: float
    error: Optional[str] = None

@dataclass
class LyricsAnalysis:
    """LLM analysis of lyrics vs theme"""
    theme_relevance_score: float
    confidence: float
    key_themes: List[str]
    reasoning: str
    lyrical_content_type: str  # narrative, emotional, abstract, descriptive, etc.

class LyricsFetcher:
    """Multi-source lyrics fetching with caching and fallbacks"""
    
    def __init__(self):
        # Try both possible token names for compatibility
        self.genius_token = os.getenv('GENIUS_CLIENT_ACCESS_TOKEN') or os.getenv('GENIUS_ACCESS_TOKEN')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Setup lyrics cache database
        self._setup_lyrics_cache()
        
    def _setup_lyrics_cache(self):
        """Create lyrics cache table"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lyrics_cache (
                    song_hash TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    lyrics TEXT,
                    source TEXT,
                    confidence REAL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to setup lyrics cache: {e}")

    def _get_song_hash(self, title: str, artist: str) -> str:
        """Generate hash for song caching"""
        normalized = f"{title.lower().strip()}_{artist.lower().strip()}"
        return hashlib.md5(normalized.encode()).hexdigest()

    def _get_cached_lyrics(self, title: str, artist: str) -> Optional[LyricsResult]:
        """Get lyrics from cache"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            song_hash = self._get_song_hash(title, artist)
            
            cursor.execute("""
                SELECT lyrics, source, confidence 
                FROM lyrics_cache 
                WHERE song_hash = ? AND lyrics IS NOT NULL
            """, (song_hash,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return LyricsResult(
                    lyrics=row['lyrics'],
                    source=row['source'],
                    confidence=row['confidence']
                )
        except Exception as e:
            logger.error(f"Cache lookup failed: {e}")
        
        return None

    def _cache_lyrics(self, title: str, artist: str, result: LyricsResult):
        """Cache lyrics result"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            song_hash = self._get_song_hash(title, artist)
            
            cursor.execute("""
                INSERT OR REPLACE INTO lyrics_cache 
                (song_hash, title, artist, lyrics, source, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (song_hash, title, artist, result.lyrics, result.source, result.confidence))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")

    def _fetch_from_genius_api(self, title: str, artist: str) -> Optional[LyricsResult]:
        """Fetch lyrics using Genius API (requires token)"""
        if not self.genius_token:
            return None
            
        try:
            # Direct API approach since lyricsgenius has endpoint issues
            headers = {'Authorization': f'Bearer {self.genius_token}'}
            
            # Search for the song
            search_response = self.session.get(
                'https://api.genius.com/search',
                params={'q': f'{title} {artist}'},
                headers=headers,
                timeout=10
            )
            
            if search_response.status_code == 200:
                data = search_response.json()
                hits = data.get('response', {}).get('hits', [])
                
                if hits:
                    # Get the best match
                    song_url = hits[0]['result']['url']
                    
                    # Scrape lyrics from the Genius page
                    page_response = self.session.get(song_url, timeout=10)
                    if page_response.status_code == 200:
                        soup = BeautifulSoup(page_response.content, 'html.parser')
                        
                        # Find lyrics container
                        lyrics_divs = soup.find_all('div', {'data-lyrics-container': 'true'})
                        if lyrics_divs:
                            lyrics_parts = []
                            for div in lyrics_divs:
                                # Get text and preserve line breaks
                                text = div.get_text(separator='\n', strip=True)
                                lyrics_parts.append(text)
                            
                            lyrics = '\n\n'.join(lyrics_parts)
                            
                            if lyrics and len(lyrics) > 50:
                                return LyricsResult(
                                    lyrics=lyrics,
                                    source="genius_api",
                                    confidence=0.9
                                )
                        
        except Exception as e:
            logger.warning(f"Genius API error: {e}")
            
        return None

    def _fetch_from_azlyrics_scrape(self, title: str, artist: str) -> Optional[LyricsResult]:
        """Fallback: scrape from AZLyrics (with rate limiting)"""
        try:
            # Clean artist and title for URL
            artist_clean = re.sub(r'[^a-zA-Z0-9]', '', artist.lower())
            title_clean = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
            
            # AZLyrics URL format
            url = f"https://www.azlyrics.com/lyrics/{artist_clean}/{title_clean}.html"
            
            # Rate limiting for politeness
            time.sleep(3)
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find lyrics div (AZLyrics specific selector)
                lyrics_div = soup.find('div', class_=None, id=None)
                if lyrics_div:
                    # Look for div that contains lyrics (usually after ringtone div)
                    lyrics_candidates = soup.find_all('div')
                    for div in lyrics_candidates:
                        if div.get_text(strip=True) and len(div.get_text(strip=True)) > 100:
                            text = div.get_text(separator='\n', strip=True)
                            # Basic validation - should contain common lyrical patterns
                            if any(word in text.lower() for word in ['verse', 'chorus', '\n\n']) or len(text) > 200:
                                return LyricsResult(
                                    lyrics=text,
                                    source="azlyrics_scrape",
                                    confidence=0.7
                                )
                                
        except Exception as e:
            logger.warning(f"AZLyrics scraping failed: {e}")
            
        return None

    def _generate_mock_lyrics_analysis(self, title: str, artist: str) -> Optional[LyricsResult]:
        """Generate mock lyrics for testing when no source available"""
        # Only for development/testing - generates plausible lyrical themes
        mock_lyrics = f"""
        [Mock lyrics for analysis purposes]
        Song: {title} by {artist}
        
        This is a placeholder representing the general thematic content
        that might be found in a song with this title and artist.
        Used for testing lyrical theme analysis when actual lyrics unavailable.
        """
        
        return LyricsResult(
            lyrics=mock_lyrics,
            source="mock_fallback",
            confidence=0.3
        )

    def fetch_lyrics(self, title: str, artist: str, enable_scraping: bool = False) -> LyricsResult:
        """Fetch lyrics with multiple fallback sources"""
        
        # Check cache first
        cached = self._get_cached_lyrics(title, artist)
        if cached:
            logger.info(f"Using cached lyrics for {title} by {artist}")
            return cached
        
        # Try Genius API first (most reliable)
        if self.genius_token:
            logger.info(f"Trying Genius API for {title} by {artist}")
            result = self._fetch_from_genius_api(title, artist)
            if result:
                self._cache_lyrics(title, artist, result)
                return result
        
        # Try scraping if enabled (be respectful with rate limiting)
        if enable_scraping:
            logger.info(f"Trying AZLyrics scraping for {title} by {artist}")
            result = self._fetch_from_azlyrics_scrape(title, artist)
            if result:
                self._cache_lyrics(title, artist, result)
                return result
        
        # Final fallback for testing
        logger.warning(f"No lyrics found for {title} by {artist}, using mock analysis")
        result = self._generate_mock_lyrics_analysis(title, artist)
        self._cache_lyrics(title, artist, result)
        return result

class LyricsAnalyzer:
    """LLM-based analysis of lyrics vs themes"""
    
    def __init__(self, verbose: bool = False):
        self.anthropic_client = None
        self.cached_client = None
        if os.getenv('ANTHROPIC_API_KEY'):
            self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            self.cached_client = CachedAnthropicClient(verbose=verbose)
    
    def analyze_lyrics_theme_match(self, lyrics: str, theme_title: str, 
                                  theme_description: str = "") -> LyricsAnalysis:
        """Analyze how well lyrics match a theme using LLM"""
        
        if not self.cached_client:
            return self._fallback_analysis(lyrics, theme_title)
        
        # Truncate lyrics if too long (to fit in context window)
        if len(lyrics) > 2000:
            lyrics = lyrics[:2000] + "..."
        
        prompt = f"""
        Analyze how well these song lyrics match the Music League theme:

        Theme: "{theme_title}"
        Description: "{theme_description}"

        Lyrics:
        {lyrics}

        Please analyze:
        1. How relevant are the lyrics to this theme? (0.0-1.0 score)
        2. What key themes/concepts appear in the lyrics?
        3. What type of lyrical content is this? (narrative, emotional, abstract, descriptive, etc.)
        4. Your confidence in this analysis (0.0-1.0)
        5. Reasoning for the relevance score

        Respond in JSON format:
        {{
            "theme_relevance_score": 0.0-1.0,
            "confidence": 0.0-1.0, 
            "key_themes": ["theme1", "theme2"],
            "lyrical_content_type": "content type",
            "reasoning": "explanation"
        }}
        """
        
        try:
            response_text = self.cached_client.create_message_simple(
                prompt=prompt,
                model="claude-3-5-sonnet-latest",
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis_json = json.loads(json_match.group(0))
                return LyricsAnalysis(
                    theme_relevance_score=analysis_json.get('theme_relevance_score', 0.5),
                    confidence=analysis_json.get('confidence', 0.5),
                    key_themes=analysis_json.get('key_themes', []),
                    reasoning=analysis_json.get('reasoning', 'LLM analysis'),
                    lyrical_content_type=analysis_json.get('lyrical_content_type', 'unknown')
                )
                
        except Exception as e:
            logger.error(f"LLM lyrics analysis failed: {e}")
        
        return self._fallback_analysis(lyrics, theme_title)
    
    def _fallback_analysis(self, lyrics: str, theme_title: str) -> LyricsAnalysis:
        """Simple keyword-based fallback analysis"""
        
        lyrics_lower = lyrics.lower()
        theme_words = set(theme_title.lower().split())
        
        # Count theme word matches
        matches = sum(1 for word in theme_words if word in lyrics_lower)
        score = min(0.8, matches / max(len(theme_words), 1) * 0.8)
        
        return LyricsAnalysis(
            theme_relevance_score=score,
            confidence=0.4,
            key_themes=list(theme_words),
            reasoning=f"Keyword matching: {matches}/{len(theme_words)} theme words found",
            lyrical_content_type="unknown"
        )

class LyricsThemeAnalyzer:
    """Main class combining lyrics fetching and analysis"""
    
    def __init__(self, enable_scraping: bool = False, verbose: bool = False):
        self.fetcher = LyricsFetcher()
        self.analyzer = LyricsAnalyzer(verbose=verbose)
        self.enable_scraping = enable_scraping
    
    def analyze_song_lyrics(self, title: str, artist: str, theme_title: str,
                           theme_description: str = "") -> Dict[str, Any]:
        """Complete lyrics analysis pipeline"""
        
        # Fetch lyrics
        lyrics_result = self.fetcher.fetch_lyrics(title, artist, self.enable_scraping)
        
        if not lyrics_result.lyrics:
            return {
                'lyrics_found': False,
                'error': 'No lyrics available',
                'theme_relevance_score': 0.0,
                'confidence': 0.0
            }
        
        # Analyze theme matching
        analysis = self.analyzer.analyze_lyrics_theme_match(
            lyrics_result.lyrics, theme_title, theme_description
        )
        
        # Combine results
        return {
            'lyrics_found': True,
            'lyrics_source': lyrics_result.source,
            'lyrics_confidence': lyrics_result.confidence,
            'theme_relevance_score': analysis.theme_relevance_score,
            'analysis_confidence': analysis.confidence,
            'key_themes': analysis.key_themes,
            'lyrical_content_type': analysis.lyrical_content_type,
            'reasoning': analysis.reasoning,
            'overall_confidence': (lyrics_result.confidence + analysis.confidence) / 2
        }

def main():
    """Demo the lyrics analysis system"""
    logging.basicConfig(level=logging.INFO)
    
    analyzer = LyricsThemeAnalyzer(enable_scraping=False)  # Set to True to enable scraping
    
    # Test with some example songs
    test_cases = [
        {"title": "Hotel California", "artist": "Eagles", "theme": "Songs about places"},
        {"title": "Bohemian Rhapsody", "artist": "Queen", "theme": "Epic rock anthems"},
        {"title": "Yesterday", "artist": "The Beatles", "theme": "Songs about time"}
    ]
    
    for test in test_cases:
        print(f"\nAnalyzing: {test['title']} by {test['artist']}")
        print(f"Theme: {test['theme']}")
        print("-" * 50)
        
        result = analyzer.analyze_song_lyrics(
            test['title'], test['artist'], test['theme']
        )
        
        if result['lyrics_found']:
            print(f"✅ Lyrics found via: {result['lyrics_source']}")
            print(f"📊 Theme relevance: {result['theme_relevance_score']:.2f}")
            print(f"🎯 Confidence: {result['overall_confidence']:.2f}")
            print(f"📝 Content type: {result['lyrical_content_type']}")
            print(f"💭 Key themes: {', '.join(result['key_themes'])}")
            print(f"🧠 Reasoning: {result['reasoning']}")
        else:
            print(f"❌ {result['error']}")

if __name__ == "__main__":
    main()
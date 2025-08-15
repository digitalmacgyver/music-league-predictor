#!/usr/bin/env ./venv/bin/python3
"""
Scout: Music League Song Recommendation Engine

Automatically discovers and recommends candidate songs for any theme
using historical data, LLM analysis, and predictive scoring.
"""

import argparse
import sys
import json
import csv
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict
import re

from forecasting import MusicForecaster, SongMatch
from setup_db import get_db_connection
from voter_preferences import VoterPreferenceModeler
from preference_forecaster import GroupPreferenceForecaster
from ensemble_forecasting import EnsembleForecaster
from lyrics_discovery import LyricsDiscoveryEngine

logger = logging.getLogger(__name__)

class SongScout:
    """Intelligent song discovery and recommendation system"""
    
    def __init__(self, verbose: bool = False, enable_voter_preferences: bool = False, 
                 enable_historical_patterns: bool = False, enable_ensemble_models: bool = True,
                 use_legacy_scoring: bool = False, enable_lyrics_discovery: bool = True):
        self.forecaster = MusicForecaster()
        self.conn = get_db_connection()
        self.verbose = verbose
        self.voter_modeler = None
        self.preference_forecaster = None
        self.group_forecast = None
        self.ensemble_forecaster = None
        self.use_legacy_scoring = use_legacy_scoring
        self.lyrics_discovery = None
        
        # Initialize voter preference modeling if requested
        if enable_voter_preferences:
            if self.verbose:
                print("🧠 Initializing voter preference modeling...")
            self.voter_modeler = VoterPreferenceModeler()
            try:
                df = self.voter_modeler.load_voting_data()
                self.voter_modeler.build_voter_song_matrix(df)
                self.voter_modeler.build_voter_profiles(df)
                self.voter_modeler.calculate_voter_similarity()
                if self.verbose:
                    print(f"   ✅ Voter preferences loaded for {len(self.voter_modeler.voter_profiles)} voters")
            except Exception as e:
                if self.verbose:
                    print(f"   ❌ Voter preference initialization failed: {e}")
                self.voter_modeler = None
        
        # Initialize historical pattern analysis if requested
        if enable_historical_patterns:
            if self.verbose:
                print("📊 Initializing historical pattern analysis...")
            try:
                self.preference_forecaster = GroupPreferenceForecaster()
                self.preference_forecaster.calculate_voter_influence_scores()
                self.preference_forecaster.build_turnover_impact_model()
                
                # Get current group forecast
                self.group_forecast = self.preference_forecaster.predict_preference_shift()
                
                if self.verbose:
                    tendency = 'conservative' if self.group_forecast['predicted_generosity_shift'] < -0.1 else 'generous' if self.group_forecast['predicted_generosity_shift'] > 0.1 else 'balanced'
                    print(f"   ✅ Historical patterns loaded - Group tendency: {tendency}")
                    print(f"   📈 Confidence: {self.group_forecast['confidence']:.1%}")
            except Exception as e:
                if self.verbose:
                    print(f"   ❌ Historical pattern initialization failed: {e}")
                self.preference_forecaster = None
        
        # Initialize ensemble models if requested
        if enable_ensemble_models:
            if self.verbose:
                print("🤖 Initializing ensemble prediction models...")
            try:
                self.ensemble_forecaster = EnsembleForecaster()
                if self.verbose:
                    print(f"   ✅ Ensemble models initialized")
                    if enable_voter_preferences or enable_historical_patterns:
                        print(f"   🎯 Will attempt ensemble training with historical data")
            except Exception as e:
                if self.verbose:
                    print(f"   ❌ Ensemble model initialization failed: {e}")
                self.ensemble_forecaster = None
        
        # Initialize lyrics-based discovery if requested
        if enable_lyrics_discovery:
            if self.verbose:
                print("🎵 Initializing lyrics-based discovery...")
            try:
                self.lyrics_discovery = LyricsDiscoveryEngine(enable_scraping=False)
                if self.verbose:
                    print(f"   ✅ Lyrics discovery initialized")
            except Exception as e:
                if self.verbose:
                    print(f"   ❌ Lyrics discovery initialization failed: {e}")
                self.lyrics_discovery = None
        
        # Song discovery databases
        self.genre_keywords = {
            'rock': ['rock', 'guitar', 'electric', 'heavy', 'metal', 'punk', 'grunge'],
            'pop': ['pop', 'hit', 'chart', 'radio', 'mainstream', 'catchy'],
            'country': ['country', 'rural', 'farm', 'truck', 'cowboy', 'honky', 'nashville'],
            'hip-hop': ['rap', 'hip', 'hop', 'urban', 'street', 'crew', 'mc'],
            'electronic': ['electronic', 'synth', 'digital', 'techno', 'house', 'edm'],
            'folk': ['folk', 'acoustic', 'traditional', 'storytelling', 'roots'],
            'jazz': ['jazz', 'swing', 'blues', 'improvisation', 'brass'],
            'classical': ['classical', 'symphony', 'orchestra', 'opera', 'chamber']
        }
        
        # Era-based artist pools
        self.era_artists = {
            '60s': ['The Beatles', 'The Rolling Stones', 'Bob Dylan', 'The Beach Boys', 'Aretha Franklin'],
            '70s': ['Led Zeppelin', 'Queen', 'Pink Floyd', 'Fleetwood Mac', 'David Bowie'],
            '80s': ['Madonna', 'Prince', 'Michael Jackson', 'U2', 'Duran Duran'],
            '90s': ['Nirvana', 'Red Hot Chili Peppers', 'Radiohead', 'Alanis Morissette', 'Pearl Jam'],
            '00s': ['Coldplay', 'The White Stripes', 'OutKast', 'Green Day', 'Eminem'],
            '10s': ['Taylor Swift', 'Ed Sheeran', 'Adele', 'Kanye West', 'Arcade Fire'],
            '20s': ['Billie Eilish', 'Harry Styles', 'Dua Lipa', 'The Weeknd', 'Olivia Rodrigo']
        }
        
        # Extremely popular/mainstream songs to exclude when --exclude-mainstream is used
        # These are mega-hits that everyone knows and likely to be submitted by multiple people
        self.mainstream_songs = {
            # All-time mega hits
            ('bohemian rhapsody', 'queen'),
            ('stairway to heaven', 'led zeppelin'),
            ('imagine', 'john lennon'),
            ('like a rolling stone', 'bob dylan'),
            ('smells like teen spirit', 'nirvana'),
            ('billie jean', 'michael jackson'),
            ('hey jude', 'the beatles'),
            ('hotel california', 'eagles'),
            ('sweet child o\' mine', 'guns n\' roses'),
            ('don\'t stop believin\'', 'journey'),
            
            # Modern streaming giants (1B+ streams)
            ('shape of you', 'ed sheeran'),
            ('blinding lights', 'the weeknd'),
            ('someone like you', 'adele'),
            ('uptown funk', 'mark ronson'),
            ('thinking out loud', 'ed sheeran'),
            ('perfect', 'ed sheeran'),
            ('bad guy', 'billie eilish'),
            ('watermelon sugar', 'harry styles'),
            ('drivers license', 'olivia rodrigo'),
            ('good 4 u', 'olivia rodrigo'),
            ('levitating', 'dua lipa'),
            ('as it was', 'harry styles'),
            ('heat waves', 'glass animals'),
            ('stay', 'the kid laroi'),
            ('industry baby', 'lil nas x'),
            ('flowers', 'miley cyrus'),
            ('anti-hero', 'taylor swift'),
            ('unholy', 'sam smith'),
            
            # Classic rock radio staples
            ('don\'t stop me now', 'queen'),
            ('we will rock you', 'queen'),
            ('back in black', 'ac/dc'),
            ('thunderstruck', 'ac/dc'),
            ('sweet caroline', 'neil diamond'),
            ('livin\' on a prayer', 'bon jovi'),
            ('mr. brightside', 'the killers'),
            ('use somebody', 'kings of leon'),
            
            # Top 40 essentials that appear on every list
            ('rolling in the deep', 'adele'),
            ('hello', 'adele'),
            ('shake it off', 'taylor swift'),
            ('blank space', 'taylor swift'),
            ('happy', 'pharrell williams'),
            ('can\'t stop the feeling!', 'justin timberlake'),
            ('closer', 'the chainsmokers'),
            ('despacito', 'luis fonsi'),
            ('old town road', 'lil nas x'),
            ('sunflower', 'post malone'),
            
            # Wedding/party classics
            ('i wanna dance with somebody', 'whitney houston'),
            ('dancing queen', 'abba'),
            ('mr. blue sky', 'electric light orchestra'),
            ('september', 'earth, wind & fire'),
            ('i want it that way', 'backstreet boys'),
            ('everybody', 'backstreet boys'),
            ('since u been gone', 'kelly clarkson'),
            ('i will survive', 'gloria gaynor'),
            ('respect', 'aretha franklin'),
            ('what\'s up?', '4 non blondes')
        }
        
        # Extremely mainstream artists whose biggest hits should be avoided
        self.mainstream_artists = {
            'taylor swift', 'ed sheeran', 'adele', 'drake', 'justin bieber',
            'ariana grande', 'billie eilish', 'post malone', 'the weeknd',
            'dua lipa', 'harry styles', 'olivia rodrigo', 'bad bunny'
        }
        
        # Common theme patterns and associated keywords
        self.theme_patterns = {
            'color': ['red', 'blue', 'green', 'yellow', 'black', 'white', 'purple', 'pink'],
            'emotion': ['love', 'sad', 'happy', 'angry', 'lonely', 'crazy', 'wild', 'calm'],
            'time': ['night', 'day', 'morning', 'evening', 'summer', 'winter', 'spring', 'fall'],
            'place': ['city', 'country', 'home', 'road', 'street', 'town', 'california', 'new york'],
            'action': ['dance', 'run', 'walk', 'drive', 'fly', 'sing', 'play', 'work'],
            'body': ['heart', 'eyes', 'hands', 'face', 'body', 'soul', 'mind', 'skin'],
            'nature': ['rain', 'sun', 'moon', 'stars', 'ocean', 'mountain', 'river', 'fire']
        }

    def discover_candidates(self, theme: str, description: str = "", 
                          era: Optional[str] = None, genre: Optional[str] = None,
                          include_obscure: bool = False, exclude_mainstream: bool = False,
                          target_count: int = 50) -> List[Dict[str, Any]]:
        """Discover candidate songs using multiple strategies"""
        
        if self.verbose:
            print(f"🔍 Discovering candidates for theme: '{theme}'")
        
        candidates = []
        seen_songs = set()  # Track (title, artist) pairs to avoid duplicates
        
        # Strategy 1: Historical analysis
        historical_candidates = self._find_historical_matches(theme, description)
        candidates.extend(self._dedupe_candidates(historical_candidates, seen_songs))
        
        # Strategy 2: Keyword-based discovery
        keyword_candidates = self._discover_by_keywords(theme, description, era, genre)
        candidates.extend(self._dedupe_candidates(keyword_candidates, seen_songs))
        
        # Strategy 3: Genre-focused discovery
        if genre:
            genre_candidates = self._discover_by_genre(genre, theme, era)
            candidates.extend(self._dedupe_candidates(genre_candidates, seen_songs))
        
        # Strategy 4: Era-focused discovery
        if era:
            era_candidates = self._discover_by_era(era, theme, include_obscure)
            candidates.extend(self._dedupe_candidates(era_candidates, seen_songs))
        
        # Strategy 5: LLM-powered thematic discovery (NEW!)
        llm_candidates = self._discover_via_llm_knowledge(theme, description, target_count // 3)
        candidates.extend(self._dedupe_candidates(llm_candidates, seen_songs))
        
        # Strategy 6: Spotify search (if available)
        if self.forecaster.spotify:
            spotify_candidates = self._discover_via_spotify(theme, description, target_count // 4)
            candidates.extend(self._dedupe_candidates(spotify_candidates, seen_songs))
        
        # Strategy 7: Theme pattern matching
        pattern_candidates = self._discover_by_patterns(theme, description)
        candidates.extend(self._dedupe_candidates(pattern_candidates, seen_songs))
        
        # Strategy 8: Lyrics-based discovery (NEW!)
        if self.lyrics_discovery:
            lyrics_candidates = self._discover_via_lyrics(theme, description, target_count // 4)
            candidates.extend(self._dedupe_candidates(lyrics_candidates, seen_songs))
        
        # Apply mainstream filtering if requested
        if exclude_mainstream:
            pre_filter_count = len(candidates)
            candidates = self._filter_mainstream_songs(candidates)
            if self.verbose:
                filtered_count = pre_filter_count - len(candidates)
                print(f"   Filtered out {filtered_count} mainstream songs")
        
        if self.verbose:
            print(f"   Found {len(candidates)} unique candidates from all strategies")
        
        return candidates[:target_count]  # Limit to prevent overwhelming the scoring system

    def _filter_mainstream_songs(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out extremely popular/mainstream songs"""
        filtered_candidates = []
        
        for candidate in candidates:
            if not self._is_mainstream_song(candidate['title'], candidate['artist']):
                filtered_candidates.append(candidate)
            elif self.verbose:
                print(f"   Excluded mainstream: {candidate['title']} by {candidate['artist']}")
        
        return filtered_candidates

    def _is_mainstream_song(self, title: str, artist: str) -> bool:
        """Check if a song is considered extremely mainstream"""
        title_lower = title.lower().strip()
        artist_lower = artist.lower().strip()
        
        # Remove common suffixes/prefixes that might interfere with matching
        title_clean = re.sub(r'\s*-\s*(remaster|live|remix|acoustic|demo|single version).*$', '', title_lower)
        title_clean = re.sub(r'^\s*(the\s+)?', '', title_clean)  # Remove leading "the"
        
        # Check against known mainstream songs
        song_key = (title_clean, artist_lower)
        if song_key in self.mainstream_songs:
            return True
        
        # Check against mainstream artists (their biggest hits are likely mainstream)
        if artist_lower in self.mainstream_artists:
            # Additional criteria for mainstream artist songs
            return self._is_likely_mainstream_hit(title_clean, artist_lower)
        
        # Check for streaming/popularity indicators in the title
        mainstream_indicators = [
            '1 billion', 'billion streams', '500 million', 'million views',
            'most popular', 'biggest hit', 'chart topper', 'number one',
            'top 10', 'top 40', 'radio edit', 'single version'
        ]
        
        full_title = title.lower()
        if any(indicator in full_title for indicator in mainstream_indicators):
            return True
        
        return False

    def _is_likely_mainstream_hit(self, title: str, artist: str) -> bool:
        """Check if a song by a mainstream artist is likely their biggest hit"""
        
        # Known biggest hits by mainstream artists
        mainstream_hits = {
            'taylor swift': ['shake it off', 'blank space', 'bad blood', 'anti-hero', 'we are never getting back together'],
            'ed sheeran': ['shape of you', 'thinking out loud', 'perfect', 'photograph', 'castle on the hill'],
            'adele': ['rolling in the deep', 'someone like you', 'hello', 'set fire to the rain', 'when we were young'],
            'drake': ['hotline bling', 'one dance', 'gods plan', 'in my feelings', 'toosie slide'],
            'justin bieber': ['baby', 'sorry', 'love yourself', 'what do you mean', 'stay'],
            'ariana grande': ['thank u, next', '7 rings', 'problem', 'side to side', 'positions'],
            'billie eilish': ['bad guy', 'when the party\'s over', 'lovely', 'everything i wanted', 'happier than ever'],
            'post malone': ['circles', 'sunflower', 'rockstar', 'congratulations', 'white iverson'],
            'the weeknd': ['blinding lights', 'can\'t feel my face', 'the hills', 'starboy', 'earned it'],
            'dua lipa': ['levitating', 'dont start now', 'new rules', 'physical', 'one kiss'],
            'harry styles': ['watermelon sugar', 'as it was', 'golden', 'adore you', 'sign of the times'],
            'olivia rodrigo': ['drivers license', 'good 4 u', 'deja vu', 'vampire', 'brutal']
        }
        
        artist_hits = mainstream_hits.get(artist, [])
        return any(hit in title for hit in artist_hits)

    def _discover_via_llm_knowledge(self, theme: str, description: str, target_count: int) -> List[Dict[str, Any]]:
        """Use LLM's deep musical knowledge to discover thematically appropriate songs"""
        candidates = []
        
        if not self.forecaster.anthropic_client:
            if self.verbose:
                print("   LLM discovery unavailable - no Anthropic API key")
            return candidates
        
        if self.verbose:
            print(f"   🧠 Using LLM musical knowledge for thematic discovery...")
        
        try:
            # Build comprehensive discovery prompt
            prompt = f"""As a music expert with deep knowledge of songs across genres and eras, suggest songs that would fit this Music League theme:

Theme: "{theme}"
Description: "{description}"

I need songs that fit the ESSENCE and FEELING of this theme, not just literal keyword matches. Consider:

1. **Sonic Characteristics**: What musical elements (rhythm, harmony, instrumentation, production) would match this theme?
2. **Lyrical Themes**: What subject matter, emotions, or narratives align with this theme?
3. **Atmospheric Qualities**: What mood, energy, or feeling should these songs evoke?
4. **Genre Considerations**: What styles or subgenres would be most appropriate?

Please suggest 25-30 diverse songs that genuinely capture the spirit of this theme. Include:
- Mix of well-known and deeper cuts (avoid the most obvious mega-hits)
- Songs from different eras and subgenres within the theme
- Both lyrically and musically appropriate choices
- Songs that demonstrate sophisticated understanding of the theme

Format your response as a JSON array where each song is an object with:
- "title": song title
- "artist": artist name  
- "reasoning": brief explanation of why it fits the theme
- "confidence": score from 0.1 to 1.0 for how well it fits

Example format:
[
  {{"title": "Song Name", "artist": "Artist Name", "reasoning": "Brief explanation", "confidence": 0.8}},
  ...
]"""

            response = self.forecaster.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Use Sonnet for sophisticated musical knowledge
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Extract JSON from response (handle markdown code blocks)
            import re
            import json
            
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find any JSON array
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    if self.verbose:
                        print("   ❌ No JSON found in LLM response")
                    return candidates
            
            try:
                llm_suggestions = json.loads(json_text)
                
                if self.verbose:
                    print(f"   📝 LLM suggested {len(llm_suggestions)} thematic candidates")
                
                # Convert to our candidate format and check against database
                cursor = self.conn.cursor()
                
                for suggestion in llm_suggestions[:target_count]:
                    song_title = suggestion.get('title', '').strip()
                    artist = suggestion.get('artist', '').strip()
                    reasoning = suggestion.get('reasoning', 'LLM thematic match')
                    confidence = suggestion.get('confidence', 0.7)
                    
                    if not song_title or not artist:
                        continue
                    
                    # Check if this song exists in our database
                    cursor.execute("""
                        SELECT s.title, s.artist, AVG(s.final_score) as avg_score
                        FROM songs s
                        WHERE (LOWER(s.title) LIKE LOWER(?) OR LOWER(s.title) LIKE LOWER(?))
                        AND (LOWER(s.artist) LIKE LOWER(?) OR LOWER(s.artist) LIKE LOWER(?))
                        GROUP BY LOWER(s.title), LOWER(s.artist)
                        LIMIT 1
                    """, (f'%{song_title}%', f'{song_title}%', f'%{artist}%', f'{artist}%'))
                    
                    db_result = cursor.fetchone()
                    
                    if db_result:
                        # Song exists in database - use database version
                        candidates.append({
                            'title': db_result['title'],
                            'artist': db_result['artist'],
                            'source': f'llm_knowledge_db',
                            'confidence': confidence,
                            'reasoning': reasoning
                        })
                        if self.verbose:
                            print(f"     ✅ Found in DB: {db_result['title']} by {db_result['artist']}")
                    else:
                        # Song not in database - add as LLM suggestion for broader discovery
                        candidates.append({
                            'title': song_title,
                            'artist': artist,
                            'source': f'llm_knowledge_external',
                            'confidence': confidence * 0.8,  # Slight penalty for not being in our historical data
                            'reasoning': reasoning
                        })
                        if self.verbose:
                            print(f"     🆕 External suggestion: {song_title} by {artist}")
                
            except json.JSONDecodeError as e:
                if self.verbose:
                    print(f"   ❌ Failed to parse LLM JSON response: {e}")
                
        except Exception as e:
            if self.verbose:
                print(f"   ❌ LLM discovery failed: {e}")
        
        if self.verbose:
            print(f"   🎵 LLM discovery found {len(candidates)} thematic candidates")
        
        return candidates

    def _discover_via_lyrics(self, theme: str, description: str, target_count: int) -> List[Dict[str, Any]]:
        """Discover candidates through lyrical content analysis"""
        candidates = []
        
        if not self.lyrics_discovery:
            return candidates
            
        try:
            if self.verbose:
                print(f"   🎵 Searching for songs with thematically relevant lyrics...")
            
            # Get lyrical candidates from the discovery engine
            lyrical_candidates = self.lyrics_discovery.get_all_lyrical_candidates(
                theme, description, limit=target_count
            )
            
            if self.verbose:
                print(f"   📝 Lyrics engine found {len(lyrical_candidates)} potential candidates")
            
            # Convert to our candidate format
            for lc in lyrical_candidates:
                candidates.append({
                    'title': lc.title,
                    'artist': lc.artist,
                    'source': f'lyrics_{lc.discovery_method}',
                    'confidence': lc.lyrical_relevance * lc.confidence,
                    'reasoning': f"Lyrical analysis ({', '.join(lc.key_themes[:3])})"
                })
                
                if self.verbose:
                    print(f"     🎯 Lyrical match: {lc.title} by {lc.artist} (relevance: {lc.lyrical_relevance:.2f})")
        
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Lyrics discovery failed: {e}")
        
        if self.verbose:
            print(f"   🎵 Lyrics discovery found {len(candidates)} candidates")
        
        return candidates

    def _find_historical_matches(self, theme: str, description: str) -> List[Dict[str, Any]]:
        """Find songs that performed well in historically similar themes"""
        candidates = []
        
        # Look for rounds with similar titles or descriptions
        cursor = self.conn.cursor()
        theme_words = re.findall(r'\w+', theme.lower())
        
        for word in theme_words[:3]:  # Use top 3 theme words
            cursor.execute("""
                SELECT s.title, s.artist, s.final_score, r.title as round_title
                FROM songs s
                JOIN rounds r ON s.round_id = r.id
                WHERE (LOWER(r.title) LIKE ? OR LOWER(r.description) LIKE ?)
                AND s.final_score > 8
                ORDER BY s.final_score DESC
                LIMIT 10
            """, (f'%{word}%', f'%{word}%'))
            
            results = cursor.fetchall()
            for result in results:
                candidates.append({
                    'title': result['title'],
                    'artist': result['artist'],
                    'source': f'historical_match_{word}',
                    'confidence': 0.8
                })
        
        return candidates

    def _discover_by_keywords(self, theme: str, description: str, era: Optional[str], 
                            genre: Optional[str]) -> List[Dict[str, Any]]:
        """Discover songs by searching for theme keywords in titles"""
        candidates = []
        
        # Extract keywords from theme and description
        theme_text = f"{theme} {description}".lower()
        keywords = re.findall(r'\w+', theme_text)
        # Filter out common words and keep meaningful terms
        meaningful_keywords = [k for k in keywords 
                             if len(k) > 2 and k not in ['song', 'songs', 'about', 'with', 'the', 'what', 'that', 'this', 'have', 'been', 'will', 'they', 'from', 'were', 'not', 'sure', 'didn', 'author']]
        
        cursor = self.conn.cursor()
        
        if self.verbose:
            print(f"   Searching for keywords: {meaningful_keywords[:5]}")
        
        for keyword in meaningful_keywords[:5]:  # Limit to prevent too many results
            # Search in song titles
            cursor.execute("""
                SELECT DISTINCT s.title, s.artist, AVG(s.final_score) as avg_score
                FROM songs s
                WHERE LOWER(s.title) LIKE ?
                GROUP BY LOWER(s.title), LOWER(s.artist)
                HAVING avg_score > 5
                ORDER BY avg_score DESC
                LIMIT 5
            """, (f'%{keyword}%',))
            
            results = cursor.fetchall()
            if self.verbose and results:
                print(f"     Found {len(results)} songs with '{keyword}' in title")
            
            for result in results:
                candidates.append({
                    'title': result['title'],
                    'artist': result['artist'],
                    'source': f'keyword_{keyword}',
                    'confidence': 0.7
                })
            
            # Also search in artist names for this keyword
            cursor.execute("""
                SELECT s.title, s.artist, s.final_score
                FROM songs s
                WHERE LOWER(s.artist) LIKE ?
                ORDER BY s.final_score DESC
                LIMIT 3
            """, (f'%{keyword}%',))
            
            artist_results = cursor.fetchall()
            for result in artist_results:
                candidates.append({
                    'title': result['title'],
                    'artist': result['artist'],
                    'source': f'artist_keyword_{keyword}',
                    'confidence': 0.6
                })
        
        return candidates

    def _discover_by_genre(self, genre: str, theme: str, era: Optional[str]) -> List[Dict[str, Any]]:
        """Discover songs focused on a specific genre"""
        candidates = []
        
        if genre.lower() not in self.genre_keywords:
            return candidates
        
        # Get genre-specific artists from our database
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.artist, COUNT(*) as song_count, AVG(s.final_score) as avg_score
            FROM songs s
            GROUP BY LOWER(s.artist)
            HAVING song_count >= 2 AND avg_score > 6
            ORDER BY avg_score DESC, song_count DESC
            LIMIT 20
        """)
        
        popular_artists = cursor.fetchall()
        
        # Filter artists that might fit the genre (basic heuristic)
        genre_artists = []
        for artist_row in popular_artists:
            artist = artist_row['artist']
            # This is a simple heuristic - in a full system, we'd have artist genre data
            genre_artists.append(artist)
        
        # Find actual songs by these artists that might fit the genre/theme
        cursor = self.conn.cursor()
        theme_words = re.findall(r'\w+', theme.lower())
        
        for artist in genre_artists[:10]:
            # Find real songs by this artist
            cursor.execute("""
                SELECT s.title, s.artist, s.final_score
                FROM songs s
                WHERE LOWER(s.artist) LIKE ?
                ORDER BY s.final_score DESC
                LIMIT 2
            """, (f'%{artist.lower()}%',))
            
            results = cursor.fetchall()
            for result in results:
                candidates.append({
                    'title': result['title'],
                    'artist': result['artist'],
                    'source': f'genre_{genre}',
                    'confidence': 0.6
                })
            
            # If no songs found, look for songs with genre keywords in title
            if not results:
                for keyword in self.genre_keywords[genre.lower()][:2]:
                    cursor.execute("""
                        SELECT s.title, s.artist, s.final_score
                        FROM songs s
                        WHERE LOWER(s.title) LIKE ? AND LOWER(s.artist) LIKE ?
                        ORDER BY s.final_score DESC
                        LIMIT 1
                    """, (f'%{keyword}%', f'%{artist.lower()}%'))
                    
                    keyword_results = cursor.fetchall()
                    for result in keyword_results:
                        candidates.append({
                            'title': result['title'],
                            'artist': result['artist'],
                            'source': f'genre_{genre}_keyword',
                            'confidence': 0.5
                        })
        
        return candidates

    def _discover_by_era(self, era: str, theme: str, include_obscure: bool) -> List[Dict[str, Any]]:
        """Discover songs from a specific era"""
        candidates = []
        
        if era not in self.era_artists:
            return candidates
        
        era_artists = self.era_artists[era]
        theme_words = re.findall(r'\w+', theme.lower())
        
        cursor = self.conn.cursor()
        
        for artist in era_artists:
            # Find actual songs by this artist in our database
            cursor.execute("""
                SELECT s.title, s.artist, s.final_score
                FROM songs s
                WHERE LOWER(s.artist) LIKE ?
                ORDER BY s.final_score DESC
                LIMIT 3
            """, (f'%{artist.lower()}%',))
            
            results = cursor.fetchall()
            for result in results:
                candidates.append({
                    'title': result['title'],
                    'artist': result['artist'],
                    'source': f'era_{era}',
                    'confidence': 0.7
                })
        
        return candidates

    def _discover_via_spotify(self, theme: str, description: str, limit: int) -> List[Dict[str, Any]]:
        """Use Spotify search to find theme-related songs"""
        candidates = []
        
        if not self.forecaster.spotify:
            return candidates
        
        try:
            # Extract meaningful search terms (avoid generic words)
            all_text = f"{theme} {description}".lower()
            search_terms = re.findall(r'\w+', all_text)
            # Filter out common words that don't help with music search
            meaningful_terms = [term for term in search_terms 
                              if len(term) > 3 and term not in ['song', 'songs', 'music', 'about', 'with', 'that', 'this', 'what', 'they', 'have', 'been', 'were', 'will']]
            
            for term in meaningful_terms[:3]:
                if self.verbose:
                    print(f"   Searching Spotify for: '{term}'")
                
                results = self.forecaster.spotify.search(q=term, type='track', limit=limit//3)
                
                for track in results['tracks']['items']:
                    # Only include if it's not a generic title
                    track_title = track['name']
                    if not any(generic in track_title.lower() for generic in ['untitled', 'track ', 'song ']):
                        candidates.append({
                            'title': track_title,
                            'artist': track['artists'][0]['name'],
                            'source': f'spotify_{term}',
                            'confidence': 0.6
                        })
                    
        except Exception as e:
            if self.verbose:
                print(f"   Spotify search failed: {e}")
        
        return candidates

    def _discover_by_patterns(self, theme: str, description: str) -> List[Dict[str, Any]]:
        """Discover songs using common theme patterns"""
        candidates = []
        
        theme_lower = f"{theme} {description}".lower()
        
        # Check which theme patterns match
        matching_patterns = []
        for pattern, keywords in self.theme_patterns.items():
            if any(keyword in theme_lower for keyword in keywords):
                matching_patterns.append((pattern, keywords))
        
        cursor = self.conn.cursor()
        
        for pattern, keywords in matching_patterns[:2]:  # Limit patterns
            for keyword in keywords[:3]:  # Limit keywords per pattern
                cursor.execute("""
                    SELECT s.title, s.artist, s.final_score
                    FROM songs s
                    WHERE LOWER(s.title) LIKE ?
                    ORDER BY s.final_score DESC
                    LIMIT 2
                """, (f'%{keyword}%',))
                
                results = cursor.fetchall()
                for result in results:
                    candidates.append({
                        'title': result['title'],
                        'artist': result['artist'],
                        'source': f'pattern_{pattern}_{keyword}',
                        'confidence': 0.5
                    })
        
        return candidates

    def _dedupe_candidates(self, candidates: List[Dict[str, Any]], 
                         seen_songs: set) -> List[Dict[str, Any]]:
        """Remove duplicate songs"""
        unique_candidates = []
        
        for candidate in candidates:
            song_key = (candidate['title'].lower().strip(), candidate['artist'].lower().strip())
            if song_key not in seen_songs:
                seen_songs.add(song_key)
                unique_candidates.append(candidate)
        
        return unique_candidates

    def score_and_rank_with_ensemble(self, theme: str, description: str, candidates: List[Dict[str, Any]],
                                   min_score: float = 0.0, voter: Optional[str] = None) -> List[SongMatch]:
        """Score candidates using ensemble models for enhanced accuracy"""
        
        if not self.ensemble_forecaster:
            # Fallback to regular scoring
            return self.score_and_rank(theme, description, candidates, min_score, voter)
        
        if self.verbose:
            print(f"🤖 Scoring {len(candidates)} candidates with ensemble models...")
        
        # Prepare songs for ensemble prediction
        songs = []
        for candidate in candidates:
            songs.append({
                'title': candidate['title'],
                'artist': candidate['artist']
            })
        
        # Filter out previous submissions
        songs = self.forecaster.filter_previous_submissions(songs)
        
        if not songs:
            if self.verbose:
                print("   No new candidates remaining after filtering previous submissions")
            return []
        
        # Get voter preference scores if available
        voter_scores = {}
        if voter and self.voter_modeler:
            try:
                voter_predictions = self.voter_modeler.predict_voter_preferences_for_candidates(voter, songs)
                for i, pred in enumerate(voter_predictions):
                    if i < len(songs):
                        song_key = f"{songs[i]['title'].lower()}_{songs[i]['artist'].lower()}"
                        # Normalize to 0-1 scale
                        voter_scores[song_key] = (pred.predicted_score - 1) / 4
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️ Voter preference scoring failed: {e}")
        
        # Get historical adjustment
        historical_adj = 1.0
        if self.group_forecast:
            predicted_shift = self.group_forecast['predicted_generosity_shift']
            confidence = self.group_forecast['confidence']
            
            if predicted_shift < -0.15 and confidence > 0.7:
                historical_adj = 1.1  # Boost for conservative groups
            elif predicted_shift > 0.15 and confidence > 0.7:
                historical_adj = 0.95  # Slight penalty for generous groups
        
        # Get ensemble predictions
        try:
            ensemble_predictions = self.ensemble_forecaster.train_and_predict(
                songs, theme, description
            )
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Ensemble prediction failed: {e}")
            # Fallback to regular scoring
            return self.score_and_rank(theme, description, candidates, min_score, voter)
        
        # Convert to SongMatch format and filter by minimum score
        predictions = []
        for i, pred in enumerate(ensemble_predictions):
            if pred.ensemble_score >= min_score:
                # Generate comprehensive reasoning
                reasoning = f"Ensemble: {pred.ensemble_method}, "
                reasoning += f"Score: {pred.ensemble_score:.3f} (conf: {pred.ensemble_confidence:.2f}), "
                reasoning += f"Theme: {pred.theme_match_score:.2f}, Audio: {pred.audio_feature_score:.2f}"
                
                if pred.lyrical_score > 0:
                    reasoning += f", Lyrics: {pred.lyrical_score:.2f}"
                
                if pred.voter_preference_score > 0:
                    reasoning += f", Voter: {pred.voter_preference_score:.2f}"
                
                if abs(pred.historical_adjustment - 1.0) > 0.05:
                    reasoning += f", Historical: {pred.historical_adjustment:.2f}"
                
                predictions.append(SongMatch(
                    song_id=i,
                    title=pred.title,
                    artist=pred.artist,
                    theme_match_score=pred.theme_match_score,
                    audio_feature_score=pred.audio_feature_score,
                    combined_score=pred.ensemble_score,
                    reasoning=reasoning,
                    lyrical_score=pred.lyrical_score,
                    lyrical_analysis=None  # Could add this if needed
                ))
        
        if self.verbose:
            print(f"   Ranked {len(predictions)} candidates with ensemble models (min_score >= {min_score})")
            if predictions:
                best = predictions[0]
                print(f"   🎯 Top pick: {best.title} by {best.artist} (score: {best.combined_score:.3f})")
        
        return predictions

    def score_and_rank(self, theme: str, description: str, candidates: List[Dict[str, Any]],
                      min_score: float = 0.0, voter: Optional[str] = None) -> List[SongMatch]:
        """Score candidates using the forecasting system and rank them"""
        
        if self.verbose:
            print(f"🎯 Scoring {len(candidates)} candidates...")
        
        # Convert candidates to the format expected by forecasting system
        candidate_songs = []
        for candidate in candidates:
            # Estimate theme relevance based on discovery source and confidence
            base_relevance = 0.5
            if 'historical' in candidate.get('source', ''):
                base_relevance = 0.8
            elif 'keyword' in candidate.get('source', ''):
                base_relevance = 0.7
            elif 'pattern' in candidate.get('source', ''):
                base_relevance = 0.6
            
            theme_relevance = base_relevance * candidate.get('confidence', 0.5)
            
            candidate_songs.append({
                'title': candidate['title'],
                'artist': candidate['artist'],
                'theme_relevance': theme_relevance
            })
        
        # Filter out songs that have already been submitted
        candidate_songs = self.forecaster.filter_previous_submissions(candidate_songs)
        
        if not candidate_songs:
            if self.verbose:
                print("   No new candidates remaining after filtering previous submissions")
            return []
        
        # Analyze theme
        theme_analysis = self.forecaster.analyze_theme_with_llm(theme, description)
        
        # Score each candidate
        predictions = []
        for i, song in enumerate(candidate_songs):
            if self.verbose and i % 10 == 0:
                print(f"   Scoring candidate {i+1}/{len(candidate_songs)}")
            
            # Use theme_relevance if LLM/Spotify not available
            if self.forecaster.anthropic_client is None and self.forecaster.spotify is None:
                theme_score = song.get('theme_relevance', 0.5)
            else:
                theme_score = self.forecaster.calculate_theme_match_score(
                    song['title'], song['artist'], theme_analysis
                )
            
            # Get audio features
            spotify_features = self.forecaster.get_spotify_features(song['title'], song['artist'])
            audio_score = self.forecaster.calculate_audio_feature_score(spotify_features, theme_analysis)
            
            # Get voter preference score if available
            voter_score = 0.5  # Default neutral score
            voter_confidence = 0.0
            
            if voter and self.voter_modeler:
                voter_predictions = self.voter_modeler.predict_voter_preferences_for_candidates(
                    voter, [song]
                )
                if voter_predictions:
                    prediction = voter_predictions[0]
                    # Normalize to 0-1 scale (from 1-5 point scale)
                    voter_score = (prediction.predicted_score - 1) / 4
                    voter_confidence = prediction.confidence
                    if self.verbose and voter_confidence > 0.5:
                        print(f"     🎯 Voter prediction: {prediction.predicted_score:.2f}/5 ({prediction.reasoning})")
            
            # Apply historical pattern adjustments
            historical_adjustment = 1.0
            if self.group_forecast:
                # Adjust scoring based on group tendency prediction
                predicted_shift = self.group_forecast['predicted_generosity_shift']
                confidence = self.group_forecast['confidence']
                
                # Conservative groups: boost high-quality songs, penalize risky ones
                if predicted_shift < -0.15 and confidence > 0.7:
                    # For conservative groups, boost songs with strong theme match
                    if theme_score > 0.8:
                        historical_adjustment = 1.2  # Boost excellent theme matches
                    elif theme_score < 0.5:
                        historical_adjustment = 0.7  # Penalize weak theme matches
                
                # Generous groups: boost creative/interesting songs
                elif predicted_shift > 0.15 and confidence > 0.7:
                    # For generous groups, boost diverse/creative selections
                    if audio_score > 0.7:
                        historical_adjustment = 1.1  # Boost interesting audio features
                
                # Apply confidence scaling
                adjustment_strength = confidence * 0.3  # Max 30% adjustment
                historical_adjustment = 1.0 + (historical_adjustment - 1.0) * adjustment_strength
            
            # Combined score with historical patterns and voter preferences
            if voter and voter_confidence > 0.3:
                # Weight: theme (35%) + audio (25%) + voter preference (25%) + historical (15%)
                base_score = theme_score * 0.35 + audio_score * 0.25 + voter_score * 0.25
                combined_score = base_score * historical_adjustment
            else:
                # Weight: theme (50%) + audio (35%) + historical (15%)
                base_score = theme_score * 0.5 + audio_score * 0.35
                combined_score = base_score * historical_adjustment
            
            # Apply minimum score filter
            if combined_score >= min_score:
                # Generate reasoning
                reasoning = f"Discovery: {candidates[i].get('source', 'unknown')}, "
                reasoning += f"Theme: {theme_score:.2f}, Audio: {audio_score:.2f}"
                if voter and voter_confidence > 0.3:
                    reasoning += f", Voter: {voter_score:.2f} (conf: {voter_confidence:.2f})"
                if self.group_forecast and abs(historical_adjustment - 1.0) > 0.05:
                    tendency = 'conservative' if self.group_forecast['predicted_generosity_shift'] < -0.1 else 'generous'
                    reasoning += f", Historical: {historical_adjustment:.2f} ({tendency} group)"
                if spotify_features:
                    reasoning += f" (Energy: {spotify_features.energy:.2f}, Valence: {spotify_features.valence:.2f})"
                
                predictions.append(SongMatch(
                    song_id=i,
                    title=song['title'],
                    artist=song['artist'],
                    theme_match_score=theme_score,
                    audio_feature_score=audio_score,
                    combined_score=combined_score,
                    reasoning=reasoning
                ))
        
        # Sort by combined score (descending)
        predictions.sort(key=lambda x: x.combined_score, reverse=True)
        
        if self.verbose:
            print(f"   Ranked {len(predictions)} candidates (min_score >= {min_score})")
        
        return predictions

    def close(self):
        """Clean up resources"""
        if self.forecaster:
            self.forecaster.close()
        if self.voter_modeler:
            self.voter_modeler.close()
        if self.ensemble_forecaster:
            self.ensemble_forecaster.close()
        if self.lyrics_discovery:
            self.lyrics_discovery.close()
        if self.conn:
            self.conn.close()

def apply_artist_diversity_filter(recommendations: List[SongMatch], target_count: int, 
                                 allow_duplicates: bool = False, verbose: bool = False) -> List[SongMatch]:
    """Apply artist diversity filter to recommendations"""
    
    if allow_duplicates:
        return recommendations[:target_count]
    
    # Calculate max songs per artist: 1 + floor(target_count/10)
    max_per_artist = 1 + target_count // 10
    
    if verbose:
        print(f"   Applying artist diversity filter: max {max_per_artist} songs per artist")
    
    artist_counts = {}
    filtered_recommendations = []
    
    for rec in recommendations:
        artist_key = rec.artist.lower().strip()
        current_count = artist_counts.get(artist_key, 0)
        
        if current_count < max_per_artist:
            filtered_recommendations.append(rec)
            artist_counts[artist_key] = current_count + 1
            
            if len(filtered_recommendations) >= target_count:
                break
    
    if verbose and len(filtered_recommendations) != len(recommendations):
        removed_count = len(recommendations) - len(filtered_recommendations)
        print(f"   Filtered out {removed_count} songs to ensure artist diversity")
    
    return filtered_recommendations

def iterative_search_for_recommendations(scout, args, target_count: int, max_iterations: int = 3) -> List[SongMatch]:
    """Iteratively search for recommendations until we have enough"""
    
    all_recommendations = []
    iteration = 1
    candidate_multiplier = 3
    
    while len(all_recommendations) < target_count and iteration <= max_iterations:
        if args.verbose:
            print(f"🔄 Search iteration {iteration} (need {target_count - len(all_recommendations)} more songs)")
        
        # Increase search breadth with each iteration
        search_count = max((target_count - len(all_recommendations)) * candidate_multiplier, 50)
        
        # Discover candidates
        candidates = scout.discover_candidates(
            theme=args.theme,
            description=args.description,
            era=args.era,
            genre=args.genre,
            include_obscure=args.include_obscure,
            exclude_mainstream=args.exclude_mainstream,
            target_count=search_count
        )
        
        if not candidates:
            if args.verbose:
                print(f"   No new candidates found in iteration {iteration}")
            break
        
        # Score and rank candidates
        if scout.use_legacy_scoring or not scout.ensemble_forecaster:
            new_recommendations = scout.score_and_rank(
                theme=args.theme,
                description=args.description,
                candidates=candidates,
                min_score=args.min_score,
                voter=args.voter
            )
        else:
            new_recommendations = scout.score_and_rank_with_ensemble(
                theme=args.theme,
                description=args.description,
                candidates=candidates,
                min_score=args.min_score,
                voter=args.voter
            )
        
        # Filter out songs we already have
        existing_songs = {(rec.title.lower(), rec.artist.lower()) for rec in all_recommendations}
        unique_new_recs = [
            rec for rec in new_recommendations 
            if (rec.title.lower(), rec.artist.lower()) not in existing_songs
        ]
        
        # Add new unique recommendations
        all_recommendations.extend(unique_new_recs)
        
        if args.verbose:
            print(f"   Added {len(unique_new_recs)} new unique recommendations")
        
        # Increase multiplier for next iteration to cast a wider net
        candidate_multiplier += 2
        iteration += 1
    
    # Sort all recommendations by score
    all_recommendations.sort(key=lambda x: x.combined_score, reverse=True)
    
    if args.verbose:
        found_count = len(all_recommendations)
        if found_count < target_count:
            print(f"⚠️  Found {found_count} recommendations (requested {target_count})")
        else:
            print(f"✅ Found {found_count} recommendations")
    
    return all_recommendations

def output_recommendations(recommendations: List[SongMatch], output_format: str, 
                         theme: str, verbose: bool = False):
    """Output recommendations in the specified format"""
    
    if output_format == 'json':
        output_data = {
            'theme': theme,
            'recommendations': [asdict(rec) for rec in recommendations],
            'total_count': len(recommendations)
        }
        print(json.dumps(output_data, indent=2))
        
    elif output_format == 'csv':
        fieldnames = ['rank', 'title', 'artist', 'combined_score', 'theme_score', 'audio_score', 'reasoning']
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, rec in enumerate(recommendations, 1):
            writer.writerow({
                'rank': i,
                'title': rec.title,
                'artist': rec.artist,
                'combined_score': f"{rec.combined_score:.3f}",
                'theme_score': f"{rec.theme_match_score:.3f}",
                'audio_score': f"{rec.audio_feature_score:.3f}",
                'reasoning': rec.reasoning
            })
            
    else:  # text format
        print(f"\n🎵 MUSIC LEAGUE SCOUT RECOMMENDATIONS")
        print(f"Theme: {theme}")
        print("=" * 60)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.title} by {rec.artist}")
            print(f"   Combined Score: {rec.combined_score:.3f}")
            print(f"   Theme Match: {rec.theme_match_score:.3f} | Audio Features: {rec.audio_feature_score:.3f}")
            if verbose:
                print(f"   Details: {rec.reasoning}")
        
        if recommendations:
            avg_score = sum(r.combined_score for r in recommendations) / len(recommendations)
            print(f"\n📊 Average Score: {avg_score:.3f}")
            print(f"🎯 Best Pick: {recommendations[0].title} by {recommendations[0].artist}")

def main():
    parser = argparse.ArgumentParser(
        description="Scout: Intelligent Music League song recommendation system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (ensemble models and lyrics discovery enabled by default):
  ./scout.py "Songs about travel"
  ./scout.py "Summer songs" --number 15 --era 80s --voter "Drew"
  ./scout.py "Sad songs" --genre rock --min-score 0.5 --historical-patterns
  ./scout.py "Songs with colors" --description "Songs that mention colors" --verbose
  ./scout.py "Love songs" --exclude-mainstream --number 10 --voter "Joe Hayward"
  ./scout.py "Epic rock anthems" --historical-patterns --verbose
  ./scout.py "Songs about heartbreak" --verbose  # Lyrics discovery enabled by default
  ./scout.py "Simple search" --no-lyrics-discovery  # Disable lyrics discovery
  ./scout.py "Ominous themes" --legacy  # Use legacy scoring instead of ensemble models
  ./scout.py "Rock songs" --number 20 --allow-artist-duplicates  # Allow multiple songs per artist
  ./scout.py "Beatles songs" --allow-artist-duplicates  # When you want multiple from same artist
        """
    )
    
    parser.add_argument('theme', help='The Music League theme to find songs for')
    parser.add_argument('-n', '--number', type=int, default=10, 
                       help='Number of song recommendations to return (default: 10)')
    parser.add_argument('-d', '--description', default='',
                       help='Additional theme description for better analysis')
    parser.add_argument('--min-score', type=float, default=0.0,
                       help='Minimum prediction score threshold (0.0-1.0, default: 0.0)')
    parser.add_argument('--era', choices=['60s', '70s', '80s', '90s', '00s', '10s', '20s'],
                       help='Focus on songs from a specific era')
    parser.add_argument('--genre', 
                       choices=['rock', 'pop', 'country', 'hip-hop', 'electronic', 'folk', 'jazz', 'classical'],
                       help='Focus on songs from a specific genre')
    parser.add_argument('--exclude-artists', 
                       help='Comma-separated list of artists to exclude')
    parser.add_argument('--include-obscure', action='store_true',
                       help='Include less mainstream songs in discovery')
    parser.add_argument('--exclude-mainstream', action='store_true',
                       help='Exclude extremely popular songs (1B+ streams, radio classics, etc.)')
    parser.add_argument('--voter', 
                       help='Personalize recommendations for a specific voter (enables collaborative filtering)')
    parser.add_argument('--historical-patterns', action='store_true',
                       help='Enable historical pattern analysis to adapt recommendations to group evolution')
    parser.add_argument('--no-lyrics-discovery', action='store_true',
                       help='Disable lyrics-based candidate discovery (enabled by default)')
    parser.add_argument('--legacy', action='store_true',
                       help='Use legacy scoring instead of advanced ensemble models (ensemble models are now default)')
    parser.add_argument('--allow-artist-duplicates', action='store_true',
                       help='Allow multiple songs from the same artist in recommendations (default: limited to 1+floor(N/10) per artist)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed discovery and scoring process')
    parser.add_argument('-o', '--output', choices=['text', 'json', 'csv'], default='text',
                       help='Output format (default: text)')
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING)
    
    scout = None
    try:
        # Initialize scout with voter preferences, historical patterns, and ensemble models if requested
        enable_voter_prefs = bool(args.voter)
        enable_historical = args.historical_patterns
        enable_ensemble = not args.legacy
        enable_lyrics = not args.no_lyrics_discovery
        scout = SongScout(verbose=args.verbose, 
                         enable_voter_preferences=enable_voter_prefs,
                         enable_historical_patterns=enable_historical,
                         enable_ensemble_models=enable_ensemble,
                         use_legacy_scoring=args.legacy,
                         enable_lyrics_discovery=enable_lyrics)
        
        if args.verbose:
            print(f"🚀 Music League Scout initialized")
            print(f"   Theme: '{args.theme}'")
            if args.description:
                print(f"   Description: '{args.description}'")
            print(f"   Target count: {args.number}")
            if args.era:
                print(f"   Era focus: {args.era}")
            if args.genre:
                print(f"   Genre focus: {args.genre}")
            if args.exclude_mainstream:
                print(f"   Excluding mainstream hits")
            if args.include_obscure:
                print(f"   Including obscure songs")
            if args.voter:
                print(f"   Personalizing for voter: {args.voter}")
            if args.historical_patterns:
                print(f"   Using historical pattern analysis")
            if not args.no_lyrics_discovery:
                print(f"   Using lyrics-based discovery")
            else:
                print(f"   Lyrics discovery disabled")
            if not args.legacy:
                print(f"   Using advanced ensemble models")
            else:
                print(f"   Using legacy scoring")
            if not args.allow_artist_duplicates:
                max_per_artist = 1 + args.number // 10
                print(f"   Artist diversity: max {max_per_artist} songs per artist")
            else:
                print(f"   Artist diversity: unlimited (duplicates allowed)")
            print()
        
        # Use iterative search to ensure we get enough recommendations
        all_recommendations = iterative_search_for_recommendations(scout, args, args.number)
        
        if not all_recommendations:
            print("❌ No recommendations found. Try a different theme or lower the minimum score.")
            return 1
        
        # Apply artist diversity filter
        if args.verbose:
            print(f"📊 Applying final filters...")
        
        filtered_recommendations = apply_artist_diversity_filter(
            all_recommendations, 
            args.number, 
            args.allow_artist_duplicates, 
            args.verbose
        )
        
        # Ensure we have the exact number requested (or as close as possible)
        final_recommendations = filtered_recommendations[:args.number]
        
        # Output results
        output_recommendations(final_recommendations, args.output, args.theme, args.verbose)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        if scout:
            scout.close()

if __name__ == "__main__":
    sys.exit(main())
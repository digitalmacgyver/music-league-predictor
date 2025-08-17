#!/usr/bin/env ./venv/bin/python3
"""
Lyrics-Based Song Discovery for Music League

Discovers candidate songs by analyzing lyrics content for thematic relevance,
going beyond title/artist keyword matching to find hidden gems.
"""

import os
import logging
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
from collections import defaultdict

from lyrics_analysis import LyricsThemeAnalyzer
from setup_db import get_db_connection

logger = logging.getLogger(__name__)

@dataclass
class LyricalCandidate:
    """A song candidate discovered through lyrical analysis"""
    title: str
    artist: str
    lyrical_relevance: float
    key_themes: List[str]
    discovery_method: str
    confidence: float
    source: str = "lyrics_discovery"

class LyricsDiscoveryEngine:
    """Discovers songs through lyrical content analysis"""
    
    def __init__(self, enable_scraping: bool = False):
        self.lyrics_analyzer = LyricsThemeAnalyzer(enable_scraping=enable_scraping)
        self.conn = get_db_connection()
        
        # Initialize lyrics knowledge base
        self._setup_lyrics_knowledge_base()
        
    def _setup_lyrics_knowledge_base(self):
        """Create tables for lyrics-based song discovery"""
        try:
            cursor = self.conn.cursor()
            
            # Table for thematic song associations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lyrical_themes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    themes TEXT,  -- JSON array of themes
                    content_type TEXT,  -- narrative, emotional, descriptive, etc.
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(title, artist)
                )
            """)
            
            # Table for successful theme-song mappings from historical data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS successful_theme_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    theme_keywords TEXT NOT NULL,
                    successful_song_title TEXT NOT NULL,
                    successful_song_artist TEXT NOT NULL,
                    score REAL,
                    lyrical_themes TEXT,  -- JSON array
                    round_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to setup lyrics knowledge base: {e}")

    def discover_via_historical_lyrics_patterns(self, theme: str, description: str = "", 
                                               limit: int = 20) -> List[LyricalCandidate]:
        """Find songs similar to historically successful lyrical patterns"""
        
        candidates = []
        
        try:
            # Extract theme keywords
            theme_keywords = self._extract_theme_keywords(theme, description)
            
            # Find historically successful songs with similar themes
            cursor = self.conn.cursor()
            
            # Look for past successful submissions with similar lyrical themes
            cursor.execute("""
                SELECT DISTINCT s.title, s.artist, s.final_score, r.title as round_theme
                FROM songs s
                JOIN rounds r ON s.round_id = r.id
                WHERE s.final_score > 2.0  -- Above average performance
                AND (
                    s.title LIKE ? OR s.artist LIKE ? OR
                    r.title LIKE ? OR r.description LIKE ?
                )
                ORDER BY s.final_score DESC
                LIMIT ?
            """, (f"%{theme_keywords[0]}%" if theme_keywords else "%",
                  f"%{theme_keywords[0]}%" if theme_keywords else "%", 
                  f"%{theme}%", f"%{description}%", limit))
            
            historical_songs = cursor.fetchall()
            
            for song in historical_songs:
                # Find songs with similar lyrical patterns to this successful song
                similar_songs = self._find_lyrically_similar_songs(
                    song['title'], song['artist'], theme, limit=3
                )
                
                for similar in similar_songs:
                    candidates.append(LyricalCandidate(
                        title=similar['title'],
                        artist=similar['artist'],
                        lyrical_relevance=similar['similarity'],
                        key_themes=similar.get('themes', []),
                        discovery_method="historical_lyrical_pattern",
                        confidence=0.7,
                        source="lyrics_discovery"
                    ))
                    
                    if len(candidates) >= limit:
                        break
                        
                if len(candidates) >= limit:
                    break
                    
        except Exception as e:
            logger.warning(f"Historical lyrics pattern discovery failed: {e}")
            
        return candidates[:limit]

    def discover_via_reverse_lyrical_search(self, theme: str, description: str = "",
                                          limit: int = 15) -> List[LyricalCandidate]:
        """Discover songs by searching for thematic content in cached lyrics"""
        
        candidates = []
        
        try:
            # Get theme keywords and concepts
            theme_keywords = self._extract_theme_keywords(theme, description)
            
            if not theme_keywords:
                return candidates
                
            # Search cached lyrics for thematic content
            cursor = self.conn.cursor()
            
            # Search in lyrics cache for relevant content
            for keyword in theme_keywords[:3]:  # Limit to top 3 keywords
                cursor.execute("""
                    SELECT title, artist, lyrics, confidence
                    FROM lyrics_cache 
                    WHERE lyrics IS NOT NULL 
                    AND (
                        LOWER(lyrics) LIKE ? OR 
                        LOWER(lyrics) LIKE ? OR
                        LOWER(lyrics) LIKE ?
                    )
                    AND confidence > 0.5
                    ORDER BY confidence DESC
                    LIMIT ?
                """, (f"%{keyword.lower()}%", f"%{keyword.lower()}s%", 
                      f"%{keyword.lower()}ing%", limit))
                
                lyrical_matches = cursor.fetchall()
                
                for match in lyrical_matches:
                    # Quick lyrical relevance analysis
                    analysis = self.lyrics_analyzer.analyzer.analyze_lyrics_theme_match(
                        match['lyrics'], theme, description
                    )
                    
                    if analysis.theme_relevance_score > 0.3:  # Minimum relevance threshold
                        candidates.append(LyricalCandidate(
                            title=match['title'],
                            artist=match['artist'],
                            lyrical_relevance=analysis.theme_relevance_score,
                            key_themes=analysis.key_themes,
                            discovery_method="reverse_lyrical_search",
                            confidence=analysis.confidence,
                            source="lyrics_discovery"
                        ))
                        
        except Exception as e:
            logger.warning(f"Reverse lyrical search failed: {e}")
            
        return candidates[:limit]

    def discover_via_thematic_association(self, theme: str, description: str = "",
                                        limit: int = 10) -> List[LyricalCandidate]:
        """Find songs through thematic lyrical associations"""
        
        candidates = []
        
        try:
            # Use LLM to generate thematically related song suggestions
            if not self.lyrics_analyzer.analyzer.anthropic_client:
                return candidates
                
            prompt = f"""
            Generate a list of songs that would be excellent matches for this Music League theme:
            
            Theme: "{theme}"
            Description: "{description}"
            
            Focus on songs where the LYRICS (not just title) would be highly relevant to this theme.
            Consider songs that might not be obvious from the title alone but have lyrical content that matches.
            
            Provide 15 song suggestions in this format:
            Title: [Song Title]
            Artist: [Artist Name]
            Relevance: [Brief explanation of lyrical relevance]
            
            Prioritize:
            1. Songs with strong lyrical theme matches
            2. Lesser-known songs that might be overlooked
            3. Songs where lyrics tell stories or convey concepts related to the theme
            """
            
            response = self.lyrics_analyzer.analyzer.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse LLM response for song suggestions
            suggestions = self._parse_llm_song_suggestions(response.content[0].text)
            
            for suggestion in suggestions[:limit]:
                candidates.append(LyricalCandidate(
                    title=suggestion['title'],
                    artist=suggestion['artist'],
                    lyrical_relevance=0.8,  # High potential relevance
                    key_themes=[theme],
                    discovery_method="thematic_association",
                    confidence=0.7,
                    source="lyrics_discovery"
                ))
                
        except Exception as e:
            logger.warning(f"Thematic association discovery failed: {e}")
            
        return candidates

    def _extract_theme_keywords(self, theme: str, description: str = "") -> List[str]:
        """Extract key thematic concepts from theme and description"""
        
        text = f"{theme} {description}".lower()
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'about', 'song', 'songs', 'music', 'that', 'this'}
        
        # Extract meaningful words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        keywords = [word for word in words if word not in stop_words]
        
        # Return top keywords by frequency and importance
        return list(dict.fromkeys(keywords))[:5]  # Remove duplicates, keep order

    def _find_lyrically_similar_songs(self, reference_title: str, reference_artist: str,
                                    theme: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find songs with similar lyrical themes to a reference song"""
        
        # This is a simplified version - in a full implementation, you'd use
        # more sophisticated similarity matching (embedding, clustering, etc.)
        
        similar_songs = []
        
        try:
            # For now, find songs by the same artist or with similar titles
            cursor = self.conn.cursor()
            
            # Find songs by same artist
            cursor.execute("""
                SELECT DISTINCT title, artist FROM songs 
                WHERE LOWER(artist) = LOWER(?) AND LOWER(title) != LOWER(?)
                LIMIT ?
            """, (reference_artist, reference_title, limit // 2))
            
            same_artist_songs = cursor.fetchall()
            
            for song in same_artist_songs:
                similar_songs.append({
                    'title': song['title'],
                    'artist': song['artist'],
                    'similarity': 0.6,  # Moderate similarity
                    'themes': [theme]
                })
            
            # Find songs with thematically similar titles
            theme_words = self._extract_theme_keywords(theme)
            if theme_words:
                for word in theme_words[:2]:
                    cursor.execute("""
                        SELECT DISTINCT title, artist FROM songs 
                        WHERE LOWER(title) LIKE ? 
                        AND NOT (LOWER(title) = LOWER(?) AND LOWER(artist) = LOWER(?))
                        LIMIT ?
                    """, (f"%{word}%", reference_title, reference_artist, limit // 2))
                    
                    thematic_songs = cursor.fetchall()
                    
                    for song in thematic_songs:
                        similar_songs.append({
                            'title': song['title'],
                            'artist': song['artist'],
                            'similarity': 0.5,
                            'themes': [word]
                        })
                        
        except Exception as e:
            logger.warning(f"Finding similar songs failed: {e}")
            
        return similar_songs[:limit]

    def _parse_llm_song_suggestions(self, llm_response: str) -> List[Dict[str, str]]:
        """Parse LLM response into structured song suggestions"""
        
        suggestions = []
        
        try:
            lines = llm_response.split('\n')
            current_song = {}
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('Title:'):
                    if current_song:  # Save previous song
                        suggestions.append(current_song)
                    current_song = {'title': line.replace('Title:', '').strip()}
                    
                elif line.startswith('Artist:') and 'title' in current_song:
                    current_song['artist'] = line.replace('Artist:', '').strip()
                    
                elif line.startswith('Relevance:') and 'artist' in current_song:
                    current_song['relevance'] = line.replace('Relevance:', '').strip()
            
            # Add final song
            if current_song and 'title' in current_song and 'artist' in current_song:
                suggestions.append(current_song)
                
        except Exception as e:
            logger.warning(f"Failed to parse LLM suggestions: {e}")
            
        return suggestions

    def get_all_lyrical_candidates(self, theme: str, description: str = "",
                                  limit: int = 30) -> List[LyricalCandidate]:
        """Get candidates from all lyrical discovery methods"""
        
        all_candidates = []
        
        # Method 1: Historical lyrical patterns
        historical = self.discover_via_historical_lyrics_patterns(theme, description, limit // 3)
        all_candidates.extend(historical)
        
        # Method 2: Reverse lyrical search
        reverse_search = self.discover_via_reverse_lyrical_search(theme, description, limit // 3)
        all_candidates.extend(reverse_search)
        
        # Method 3: Thematic associations
        thematic = self.discover_via_thematic_association(theme, description, limit // 3)
        all_candidates.extend(thematic)
        
        # Deduplicate and sort by relevance
        seen = set()
        unique_candidates = []
        
        for candidate in all_candidates:
            song_key = (candidate.title.lower(), candidate.artist.lower())
            if song_key not in seen:
                seen.add(song_key)
                unique_candidates.append(candidate)
        
        # Sort by lyrical relevance * confidence
        unique_candidates.sort(
            key=lambda x: x.lyrical_relevance * x.confidence, 
            reverse=True
        )
        
        return unique_candidates[:limit]

    def close(self):
        """Clean up resources"""
        if self.conn:
            self.conn.close()
        if self.lyrics_analyzer:
            self.lyrics_analyzer.fetcher = None

def main():
    """Demo the lyrics discovery system"""
    logging.basicConfig(level=logging.INFO)
    
    discovery = LyricsDiscoveryEngine()
    
    # Test with example themes
    test_themes = [
        ("Songs about travel", "Songs that mention specific places or journeys"),
        ("Time-related songs", "Songs about past, future, or the passage of time"),
        ("Songs about relationships", "Love, breakups, friendship, family")
    ]
    
    for theme, description in test_themes:
        print(f"\n🎵 Discovering songs for: {theme}")
        print(f"📝 Description: {description}")
        print("-" * 60)
        
        candidates = discovery.get_all_lyrical_candidates(theme, description, limit=10)
        
        for i, candidate in enumerate(candidates, 1):
            print(f"{i}. {candidate.title} by {candidate.artist}")
            print(f"   Relevance: {candidate.lyrical_relevance:.2f} | Method: {candidate.discovery_method}")
            print(f"   Themes: {', '.join(candidate.key_themes)}")
            print()
    
    discovery.close()

if __name__ == "__main__":
    main()
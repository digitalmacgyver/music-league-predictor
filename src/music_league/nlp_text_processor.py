#!/usr/bin/env ./venv/bin/python3
"""
NLP-based Text Processing for Music League

Provides proper text processing for the three distinct contexts:
1. Conceptual Analysis - semantic similarity and theme matching
2. Matching - fuzzy matching for song/artist identification
3. Exact Identification - preservation of exact Spotify metadata

Uses established NLP libraries and techniques rather than custom regex.
"""

import re
import string
import unicodedata
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
import logging

# Try to import fuzzy matching libraries
try:
    from fuzzywuzzy import fuzz, process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    logging.warning("FuzzyWuzzy not available - install with: pip install fuzzywuzzy python-levenshtein")

# Try to import NLP libraries for semantic analysis
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
    
    # Download required NLTK data if not present
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
        
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available - install with: pip install nltk")

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Result of fuzzy matching operation"""
    score: float
    matched_text: str
    confidence: str  # 'high', 'medium', 'low'
    method: str
    
@dataclass
class ConceptualAnalysis:
    """Result of conceptual/semantic analysis"""
    relevance_score: float
    key_concepts: List[str]
    semantic_tokens: List[str]
    reasoning: str

class MusicTextProcessor:
    """
    Central text processing system for music-related text
    """
    
    def __init__(self):
        self.stemmer = PorterStemmer() if NLTK_AVAILABLE else None
        self.stop_words = set(stopwords.words('english')) if NLTK_AVAILABLE else set()
        
        # Music-specific stop words and noise terms
        self.music_stop_words = {
            'remaster', 'remastered', 'live', 'remix', 'acoustic', 'demo', 
            'single', 'version', 'radio', 'edit', 'explicit', 'deluxe',
            'extended', 'instrumental', 'karaoke', 'clean', 'dirty',
            'uncensored', 'album', 'ep', 'bonus', 'track', 'stereo', 'mono'
        }
        
        # Common title/artist prefixes that should be normalized
        self.common_prefixes = {
            'title': ["the ", "a ", "an "],
            'artist': ["the ", "dj ", "mc "]
        }
        
        # Punctuation that should be normalized vs removed
        self.normalize_punct = {
            '&': ' and ',
            '+': ' plus ',
            '@': ' at ',
            '$': ' s ',
            '%': ' percent '
        }
    
    # ===== CONCEPTUAL ANALYSIS METHODS =====
    
    def extract_semantic_concepts(self, text: str, context: str = 'theme') -> ConceptualAnalysis:
        """
        Extract semantic concepts for theme matching and discovery
        
        Used for: LLM keyword generation, theme relevance, genre classification
        """
        if not text:
            return ConceptualAnalysis(0.0, [], [], "Empty text")
        
        # Basic preprocessing
        text_clean = self._basic_clean(text)
        
        # Tokenize and extract meaningful terms
        if NLTK_AVAILABLE:
            tokens = word_tokenize(text_clean.lower())
            # Remove stop words but keep music-relevant terms
            meaningful_tokens = [
                token for token in tokens 
                if (token not in self.stop_words or token in self.music_stop_words)
                and len(token) > 2
                and token.isalpha()
            ]
            
            # Stem for concept extraction
            stemmed_concepts = [self.stemmer.stem(token) for token in meaningful_tokens]
        else:
            # Fallback without NLTK
            tokens = text_clean.lower().split()
            meaningful_tokens = [t for t in tokens if len(t) > 2 and t.isalpha()]
            stemmed_concepts = meaningful_tokens
        
        # Extract key concepts (remove duplicates, maintain order)
        key_concepts = list(dict.fromkeys(meaningful_tokens))
        
        # Calculate relevance (basic implementation - could be enhanced with embeddings)
        relevance_score = min(1.0, len(key_concepts) / 10.0)
        
        return ConceptualAnalysis(
            relevance_score=relevance_score,
            key_concepts=key_concepts[:10],  # Top 10 concepts
            semantic_tokens=stemmed_concepts,
            reasoning=f"Extracted {len(key_concepts)} concepts from {context}"
        )
    
    def calculate_theme_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts for theme matching
        
        Used for: Determining if a song title/lyrics matches a theme
        """
        concepts1 = self.extract_semantic_concepts(text1)
        concepts2 = self.extract_semantic_concepts(text2)
        
        if not concepts1.key_concepts or not concepts2.key_concepts:
            return 0.0
        
        # Simple Jaccard similarity on concepts
        set1 = set(concepts1.semantic_tokens)
        set2 = set(concepts2.semantic_tokens)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    # ===== MATCHING METHODS =====
    
    def normalize_for_matching(self, text: str, text_type: str = 'title') -> str:
        """
        Normalize text for fuzzy matching operations
        
        Used for: Spotify search, database lookups, deduplication
        """
        if not text:
            return ""
        
        # Basic cleaning
        normalized = self._basic_clean(text)
        
        # Remove music-specific suffixes
        normalized = self._remove_music_suffixes(normalized)
        
        # Handle common prefixes for specific text types
        if text_type in self.common_prefixes:
            for prefix in self.common_prefixes[text_type]:
                if normalized.lower().startswith(prefix):
                    normalized = normalized[len(prefix):].strip()
                    break
        
        # Normalize punctuation
        for punct, replacement in self.normalize_punct.items():
            normalized = normalized.replace(punct, replacement)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def fuzzy_match_songs(self, query_title: str, query_artist: str, 
                         candidates: List[Tuple[str, str]]) -> List[MatchResult]:
        """
        Fuzzy match a song against candidate songs
        
        Used for: Spotify verification, database matching
        Returns: Sorted list of matches (best first)
        """
        if not FUZZYWUZZY_AVAILABLE:
            return self._fallback_fuzzy_match(query_title, query_artist, candidates)
        
        # Normalize inputs
        norm_query_title = self.normalize_for_matching(query_title, 'title')
        norm_query_artist = self.normalize_for_matching(query_artist, 'artist')
        
        results = []
        
        for candidate_title, candidate_artist in candidates:
            norm_cand_title = self.normalize_for_matching(candidate_title, 'title')
            norm_cand_artist = self.normalize_for_matching(candidate_artist, 'artist')
            
            # Multiple fuzzy matching approaches
            title_ratio = fuzz.ratio(norm_query_title.lower(), norm_cand_title.lower())
            title_partial = fuzz.partial_ratio(norm_query_title.lower(), norm_cand_title.lower())
            title_token_sort = fuzz.token_sort_ratio(norm_query_title.lower(), norm_cand_title.lower())
            title_token_set = fuzz.token_set_ratio(norm_query_title.lower(), norm_cand_title.lower())
            
            artist_ratio = fuzz.ratio(norm_query_artist.lower(), norm_cand_artist.lower())
            
            # Weighted composite score (title more important than artist)
            title_score = max(title_ratio, title_partial, title_token_sort, title_token_set)
            composite_score = (title_score * 0.7 + artist_ratio * 0.3)
            
            # Determine confidence level
            if composite_score >= 90:
                confidence = 'high'
            elif composite_score >= 75:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            results.append(MatchResult(
                score=composite_score / 100.0,  # Normalize to 0-1
                matched_text=f"{candidate_title} by {candidate_artist}",
                confidence=confidence,
                method="fuzzywuzzy_composite"
            ))
        
        # Sort by score descending
        return sorted(results, key=lambda x: x.score, reverse=True)
    
    def create_deduplication_key(self, title: str, artist: str) -> str:
        """
        Create a normalized key for deduplication
        
        Used for: Removing duplicate candidates
        """
        norm_title = self.normalize_for_matching(title, 'title').lower()
        norm_artist = self.normalize_for_matching(artist, 'artist').lower()
        
        # Remove all punctuation for dedup
        norm_title = re.sub(r'[^\w\s]', '', norm_title)
        norm_artist = re.sub(r'[^\w\s]', '', norm_artist)
        
        # Sort words to handle reordering
        title_words = sorted(norm_title.split())
        artist_words = sorted(norm_artist.split())
        
        return f"{'_'.join(title_words)}|{'_'.join(artist_words)}"
    
    # ===== EXACT IDENTIFICATION METHODS =====
    
    def preserve_exact_metadata(self, spotify_track: Dict) -> Dict[str, str]:
        """
        Extract and preserve exact Spotify metadata
        
        Used for: Final playlist creation, user display
        """
        return {
            'spotify_id': spotify_track.get('id', ''),
            'exact_title': spotify_track.get('name', ''),
            'exact_artist': spotify_track['artists'][0]['name'] if spotify_track.get('artists') else '',
            'album': spotify_track.get('album', {}).get('name', ''),
            'release_date': spotify_track.get('album', {}).get('release_date', ''),
            'external_url': spotify_track.get('external_urls', {}).get('spotify', ''),
            'uri': spotify_track.get('uri', '')
        }
    
    # ===== HELPER METHODS =====
    
    def _basic_clean(self, text: str) -> str:
        """Basic text cleaning"""
        if not text:
            return ""
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove leading/trailing quotes
        text = re.sub(r'^["\'\"`''""„‚]+|["\'\"`''""„‚]+$', '', text.strip())
        
        return text.strip()
    
    def _remove_music_suffixes(self, text: str) -> str:
        """Remove common music suffixes for matching"""
        # Only remove music suffixes that are:
        # 1. At the end of the text (word boundary)
        # 2. Enclosed in brackets/parentheses, OR
        # 3. Preceded by delimiter and at end
        
        # Pattern 1: Remove bracketed suffixes like "(Remastered)", "[Live]", "- Demo"
        bracketed_pattern = r'\s*[-–—]\s*\([^)]*(' + '|'.join(self.music_stop_words) + r')[^)]*\)$'
        bracketed_pattern += r'|\s*\([^)]*(' + '|'.join(self.music_stop_words) + r')[^)]*\)$'
        bracketed_pattern += r'|\s*\[[^\]]*(' + '|'.join(self.music_stop_words) + r')[^\]]*\]$'
        
        # Pattern 2: Remove dash/hyphen suffixes like "- Remastered", "– Live Version"
        dash_pattern = r'\s*[-–—]\s*(' + '|'.join(self.music_stop_words) + r')(\s+\w+)*$'
        
        # Apply patterns
        text = re.sub(bracketed_pattern, '', text, flags=re.IGNORECASE)
        text = re.sub(dash_pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _fallback_fuzzy_match(self, query_title: str, query_artist: str, 
                            candidates: List[Tuple[str, str]]) -> List[MatchResult]:
        """Fallback matching without FuzzyWuzzy"""
        norm_query = f"{self.normalize_for_matching(query_title)} {self.normalize_for_matching(query_artist)}".lower()
        
        results = []
        for candidate_title, candidate_artist in candidates:
            norm_candidate = f"{self.normalize_for_matching(candidate_title)} {self.normalize_for_matching(candidate_artist)}".lower()
            
            # Use difflib for basic similarity
            score = SequenceMatcher(None, norm_query, norm_candidate).ratio()
            
            confidence = 'high' if score >= 0.9 else 'medium' if score >= 0.7 else 'low'
            
            results.append(MatchResult(
                score=score,
                matched_text=f"{candidate_title} by {candidate_artist}",
                confidence=confidence,
                method="difflib_fallback"
            ))
        
        return sorted(results, key=lambda x: x.score, reverse=True)


def main():
    """Demo the NLP text processing system"""
    processor = MusicTextProcessor()
    
    print("🎵 Music NLP Text Processor Demo")
    print("=" * 50)
    
    # Test conceptual analysis
    theme = "Songs about food and eating"
    song_title = "It's Raining Tacos"
    
    print(f"\n1. Conceptual Analysis:")
    print(f"Theme: {theme}")
    print(f"Song: {song_title}")
    
    theme_concepts = processor.extract_semantic_concepts(theme, 'theme')
    song_concepts = processor.extract_semantic_concepts(song_title, 'song')
    similarity = processor.calculate_theme_similarity(theme, song_title)
    
    print(f"Theme concepts: {theme_concepts.key_concepts}")
    print(f"Song concepts: {song_concepts.key_concepts}")
    print(f"Similarity: {similarity:.3f}")
    
    # Test matching
    print(f"\n2. Fuzzy Matching:")
    query_title = "It's Raining Tacos"
    query_artist = "Parry Gripp"
    
    candidates = [
        ("Raining Tacos", "Parry Gripp"),
        ("It's Raining Tacos Again", "Parry Gripp"),
        ("Raining Tacos", "CoComelon"),
        ("Taco Tuesday", "Parry Gripp")
    ]
    
    matches = processor.fuzzy_match_songs(query_title, query_artist, candidates)
    
    print(f"Query: {query_title} by {query_artist}")
    print("Matches:")
    for i, match in enumerate(matches[:3], 1):
        print(f"  {i}. {match.matched_text} (score: {match.score:.3f}, confidence: {match.confidence})")
    
    # Test normalization
    print(f"\n3. Normalization:")
    test_titles = [
        "It's Raining Tacos",
        "November Rain (2008 Remaster)",
        "Yesterday - Live at Abbey Road",
        "Don't Stop Me Now!!!"
    ]
    
    for title in test_titles:
        normalized = processor.normalize_for_matching(title, 'title')
        print(f"  '{title}' -> '{normalized}'")
    
    # Test deduplication
    print(f"\n4. Deduplication Keys:")
    test_pairs = [
        ("Hotel California", "Eagles"),
        ("Hotel California - Live", "The Eagles"),
        ("Hotel California (2013 Remaster)", "Eagles")
    ]
    
    for title, artist in test_pairs:
        key = processor.create_deduplication_key(title, artist)
        print(f"  '{title}' by '{artist}' -> '{key}'")

if __name__ == "__main__":
    main()
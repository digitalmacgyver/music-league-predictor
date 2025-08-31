#!/usr/bin/env ./venv/bin/python3
"""
Scout NLP Integration

Updates Scout to use proper NLP techniques for:
- Conceptual theme analysis (semantic similarity)
- Fuzzy matching for candidate discovery
- Clean separation of discovery vs verification
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from music_league.nlp_text_processor import MusicTextProcessor, ConceptualAnalysis
from candidate_verification_nlp import NLPCandidateVerifier

logger = logging.getLogger(__name__)

@dataclass
class ThemeAnalysis:
    """Enhanced theme analysis using NLP"""
    theme_title: str
    theme_description: str
    key_concepts: List[str]
    semantic_keywords: List[str]
    genre_hints: List[str]
    mood_indicators: List[str]
    conceptual_score: float

class ScoutNLPAnalyzer:
    """
    NLP-enhanced analysis for Scout theme matching
    
    Handles CONCEPTUAL ANALYSIS for theme understanding and song discovery
    """
    
    def __init__(self):
        self.text_processor = MusicTextProcessor()
        self.verifier = NLPCandidateVerifier()
        
        # Enhanced genre/mood patterns using semantic concepts
        self.semantic_patterns = {
            'energy_level': {
                'high': ['rock', 'metal', 'punk', 'dance', 'electronic', 'energetic', 'intense', 'loud', 'fast'],
                'medium': ['pop', 'alternative', 'indie', 'folk', 'acoustic', 'moderate', 'steady'],
                'low': ['ambient', 'chill', 'slow', 'peaceful', 'calm', 'quiet', 'soft', 'gentle']
            },
            'emotional_tone': {
                'happy': ['joy', 'celebration', 'party', 'fun', 'upbeat', 'cheerful', 'positive'],
                'sad': ['melancholy', 'sorrow', 'loss', 'heartbreak', 'tears', 'grief', 'lonely'],
                'angry': ['rage', 'fury', 'protest', 'rebellion', 'aggressive', 'hostile'],
                'romantic': ['love', 'romance', 'heart', 'relationship', 'passion', 'intimate'],
                'nostalgic': ['memory', 'past', 'remember', 'yesterday', 'old', 'vintage', 'classic']
            },
            'thematic_content': {
                'travel': ['road', 'journey', 'destination', 'highway', 'adventure', 'explore', 'wanderlust'],
                'nature': ['mountain', 'ocean', 'forest', 'sky', 'earth', 'natural', 'outdoor', 'wildlife'],
                'urban': ['city', 'street', 'downtown', 'metropolitan', 'urban', 'concrete', 'building'],
                'time': ['morning', 'night', 'season', 'year', 'time', 'moment', 'clock', 'calendar'],
                'color': ['red', 'blue', 'green', 'yellow', 'black', 'white', 'purple', 'rainbow'],
                'food': ['food', 'eat', 'drink', 'meal', 'hunger', 'taste', 'cooking', 'restaurant']
            }
        }
    
    def analyze_theme_semantically(self, theme_title: str, theme_description: str = "") -> ThemeAnalysis:
        """
        Perform semantic analysis of theme for enhanced discovery
        
        This is CONCEPTUAL ANALYSIS - we want to understand meaning, not exact matches
        """
        # Extract semantic concepts from theme
        full_theme_text = f"{theme_title} {theme_description}".strip()
        concepts = self.text_processor.extract_semantic_concepts(full_theme_text, 'theme')
        
        # Identify genre/mood patterns
        genre_hints = []
        mood_indicators = []
        
        theme_lower = full_theme_text.lower()
        
        # Check for genre/energy patterns
        for energy, keywords in self.semantic_patterns['energy_level'].items():
            if any(keyword in theme_lower for keyword in keywords):
                genre_hints.append(f"energy_{energy}")
        
        # Check for emotional patterns
        for emotion, keywords in self.semantic_patterns['emotional_tone'].items():
            if any(keyword in theme_lower for keyword in keywords):
                mood_indicators.append(f"emotion_{emotion}")
        
        # Check for thematic content patterns
        thematic_matches = []
        for theme_type, keywords in self.semantic_patterns['thematic_content'].items():
            matches = [kw for kw in keywords if kw in theme_lower]
            if matches:
                thematic_matches.extend([f"theme_{theme_type}"] + matches)
        
        # Generate semantic keywords (expanded from core concepts)
        semantic_keywords = concepts.key_concepts.copy()
        
        # Add related terms based on patterns
        for concept in concepts.key_concepts:
            for pattern_category in self.semantic_patterns.values():
                for pattern_group, keywords in pattern_category.items():
                    if concept in keywords:
                        # Add related keywords from same group
                        semantic_keywords.extend([kw for kw in keywords if kw != concept])
        
        # Remove duplicates while preserving order
        semantic_keywords = list(dict.fromkeys(semantic_keywords))
        
        return ThemeAnalysis(
            theme_title=theme_title,
            theme_description=theme_description,
            key_concepts=concepts.key_concepts,
            semantic_keywords=semantic_keywords[:20],  # Top 20 keywords
            genre_hints=genre_hints,
            mood_indicators=mood_indicators,
            conceptual_score=concepts.relevance_score
        )
    
    def generate_discovery_keywords_nlp(self, theme_analysis: ThemeAnalysis) -> List[str]:
        """
        Generate discovery keywords using NLP analysis
        
        This replaces hard-coded keyword lists with semantic understanding
        """
        # Start with semantic keywords
        discovery_keywords = theme_analysis.semantic_keywords.copy()
        
        # Add concept variations
        for concept in theme_analysis.key_concepts:
            # Add plural/singular variations
            if concept.endswith('s') and len(concept) > 3:
                discovery_keywords.append(concept[:-1])  # Remove 's'
            elif not concept.endswith('s'):
                discovery_keywords.append(concept + 's')  # Add 's'
            
            # Add common variations
            variations = {
                'eat': ['eating', 'food', 'meal', 'dining'],
                'food': ['eat', 'meal', 'cooking', 'kitchen'],
                'love': ['romance', 'heart', 'relationship'],
                'travel': ['journey', 'road', 'adventure'],
                'time': ['moment', 'hour', 'day', 'night'],
                'music': ['song', 'sound', 'melody', 'rhythm']
            }
            
            if concept in variations:
                discovery_keywords.extend(variations[concept])
        
        # Add genre/mood based keywords
        if 'theme_food' in theme_analysis.genre_hints or any('food' in concept for concept in theme_analysis.key_concepts):
            discovery_keywords.extend(['restaurant', 'kitchen', 'recipe', 'hungry', 'delicious', 'taste'])
        
        if 'emotion_happy' in theme_analysis.mood_indicators:
            discovery_keywords.extend(['celebration', 'party', 'joy', 'smile', 'laugh'])
        
        if 'emotion_sad' in theme_analysis.mood_indicators:
            discovery_keywords.extend(['cry', 'tear', 'lonely', 'miss', 'goodbye'])
        
        # Remove duplicates and return top keywords
        discovery_keywords = list(dict.fromkeys(discovery_keywords))
        return discovery_keywords[:30]  # Top 30 discovery keywords
    
    def calculate_song_theme_relevance_nlp(self, song_title: str, song_artist: str, 
                                          theme_analysis: ThemeAnalysis) -> float:
        """
        Calculate how well a song matches a theme using semantic similarity
        
        This is CONCEPTUAL ANALYSIS - semantic matching, not exact string matching
        """
        # Extract song concepts
        song_text = f"{song_title} {song_artist}"
        song_concepts = self.text_processor.extract_semantic_concepts(song_text, 'song')
        
        # Calculate semantic similarity with theme
        theme_text = f"{theme_analysis.theme_title} {theme_analysis.theme_description}"
        semantic_similarity = self.text_processor.calculate_theme_similarity(song_text, theme_text)
        
        # Check for keyword matches (conceptual, not exact)
        keyword_matches = 0
        song_lower = song_text.lower()
        
        for keyword in theme_analysis.semantic_keywords:
            if keyword.lower() in song_lower:
                keyword_matches += 1
        
        keyword_score = min(1.0, keyword_matches / max(len(theme_analysis.semantic_keywords), 1))
        
        # Combine scores with weights
        # Semantic similarity is more important than exact keyword matches
        relevance_score = (semantic_similarity * 0.7 + keyword_score * 0.3)
        
        return relevance_score
    
    def enhance_candidates_with_nlp(self, candidates: List[Dict[str, Any]], 
                                   theme_analysis: ThemeAnalysis, 
                                   verify_external: bool = True) -> List[Dict[str, Any]]:
        """
        Enhance candidates with NLP-based scoring and verification
        
        Combines CONCEPTUAL ANALYSIS (theme relevance) with MATCHING (verification)
        """
        if not candidates:
            return []
        
        # First, calculate NLP-based theme relevance scores
        for candidate in candidates:
            title = candidate.get('title', '')
            artist = candidate.get('artist', '')
            
            # Calculate semantic relevance
            nlp_relevance = self.calculate_song_theme_relevance_nlp(title, artist, theme_analysis)
            
            # Update confidence based on NLP analysis
            original_confidence = candidate.get('confidence', 0.5)
            # Boost confidence if high semantic relevance
            if nlp_relevance > 0.7:
                enhanced_confidence = min(1.0, original_confidence * 1.2)
            elif nlp_relevance > 0.4:
                enhanced_confidence = original_confidence
            else:
                enhanced_confidence = original_confidence * 0.8
            
            candidate['nlp_theme_relevance'] = nlp_relevance
            candidate['confidence'] = enhanced_confidence
        
        # Then verify with Spotify using NLP matching
        verified_candidates = self.verifier.validate_candidate_list_nlp(
            candidates, verify_external=verify_external, verbose=False
        )
        
        return verified_candidates


def main():
    """Demo the Scout NLP integration"""
    logging.basicConfig(level=logging.INFO)
    
    analyzer = ScoutNLPAnalyzer()
    
    print("🎵 Scout NLP Integration Demo")
    print("=" * 50)
    
    # Test theme analysis
    theme_title = "Music about meals/eating/food (NO Weird Al!)"
    theme_description = "Songs that reference food, cooking, eating, or meals in their lyrics or titles"
    
    print(f"\n1. Theme Analysis:")
    print(f"Theme: {theme_title}")
    print(f"Description: {theme_description}")
    
    theme_analysis = analyzer.analyze_theme_semantically(theme_title, theme_description)
    
    print(f"Key concepts: {theme_analysis.key_concepts}")
    print(f"Semantic keywords: {theme_analysis.semantic_keywords[:10]}...")
    print(f"Genre hints: {theme_analysis.genre_hints}")
    print(f"Mood indicators: {theme_analysis.mood_indicators}")
    print(f"Conceptual score: {theme_analysis.conceptual_score:.3f}")
    
    # Test discovery keywords
    print(f"\n2. Discovery Keywords:")
    discovery_keywords = analyzer.generate_discovery_keywords_nlp(theme_analysis)
    print(f"Generated {len(discovery_keywords)} keywords: {discovery_keywords[:15]}...")
    
    # Test song relevance
    print(f"\n3. Song Relevance Scoring:")
    test_songs = [
        ("It's Raining Tacos", "Parry Gripp"),
        ("Jambalaya (On the Bayou)", "Hank Williams"),
        ("Yesterday", "The Beatles"),
        ("Banana Pancakes", "Jack Johnson"),
        ("November Rain", "Guns N' Roses")
    ]
    
    for title, artist in test_songs:
        relevance = analyzer.calculate_song_theme_relevance_nlp(title, artist, theme_analysis)
        print(f"  '{title}' by {artist}: {relevance:.3f}")
    
    # Test candidate enhancement
    print(f"\n4. Candidate Enhancement:")
    test_candidates = [
        {"title": "It's Raining Tacos", "artist": "Parry Gripp", "source": "llm_knowledge_external", "confidence": 0.8},
        {"title": "Jambalaya (On the Bayou)", "artist": "Hank Williams", "source": "llm_knowledge_external", "confidence": 0.7},
        {"title": "Yesterday", "artist": "The Beatles", "source": "database", "confidence": 0.9}
    ]
    
    enhanced = analyzer.enhance_candidates_with_nlp(test_candidates, theme_analysis, verify_external=True)
    
    print(f"Enhanced {len(enhanced)} candidates:")
    for candidate in enhanced:
        nlp_score = candidate.get('nlp_theme_relevance', 0.0)
        confidence = candidate.get('confidence', 0.0)
        verification = candidate.get('verification', 'none')
        
        print(f"  '{candidate['title']}' by {candidate['artist']}")
        print(f"    NLP relevance: {nlp_score:.3f}, Confidence: {confidence:.3f}, Verification: {verification}")

if __name__ == "__main__":
    main()
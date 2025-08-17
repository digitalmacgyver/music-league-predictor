#!/usr/bin/env ./venv/bin/python3
"""
NLP-based Candidate Verification System

Replaces the regex-heavy verification with proper NLP techniques for:
- Fuzzy matching using established libraries
- Semantic text analysis for conceptual matching
- Clean separation of matching vs exact identification
"""

import os
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from nlp_text_processor import MusicTextProcessor, MatchResult

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class CandidateValidation:
    """Result of candidate verification using NLP techniques"""
    is_valid: bool
    verified_title: Optional[str] = None
    verified_artist: Optional[str] = None
    verification_method: str = "unverified"
    confidence_score: float = 0.0
    confidence_level: str = "low"  # 'high', 'medium', 'low'
    issues: List[str] = None
    spotify_metadata: Optional[Dict] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []

class NLPCandidateVerifier:
    """NLP-based candidate verification and cleaning"""
    
    def __init__(self):
        self.text_processor = MusicTextProcessor()
        self.spotify = None
        self.stats = {
            "total_candidates": 0,
            "spotify_verified": 0,
            "fuzzy_matched": 0,
            "exact_matched": 0,
            "duplicates_removed": 0,
            "invalid_removed": 0
        }
        
        # Initialize Spotify client
        if os.getenv('SPOTIFY_CLIENT_ID') and os.getenv('SPOTIFY_CLIENT_SECRET'):
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                logger.info("Spotify NLP verification initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify client: {e}")
        else:
            logger.warning("Spotify credentials not found - verification limited")
    
    def verify_with_spotify_nlp(self, title: str, artist: str) -> CandidateValidation:
        """
        Verify song exists on Spotify using NLP fuzzy matching
        
        This is MATCHING context - we want to find the best fuzzy match
        """
        if not self.spotify:
            return CandidateValidation(
                is_valid=False,
                verification_method="no_spotify",
                confidence_score=0.0,
                confidence_level="low",
                issues=["Spotify verification unavailable"]
            )
        
        try:
            # Search Spotify with multiple query strategies
            search_queries = [
                f'track:"{title}" artist:"{artist}"',  # Exact search
                f'{title} {artist}',                    # Natural search
                f'{title}',                             # Title only
                f'artist:{artist} {title}'              # Artist-focused
            ]
            
            all_candidates = []
            seen_ids = set()
            
            # Collect candidates from multiple searches
            for query in search_queries:
                try:
                    results = self.spotify.search(q=query, type='track', limit=10)
                    for track in results['tracks']['items']:
                        if track['id'] not in seen_ids:
                            all_candidates.append((
                                track['name'],
                                track['artists'][0]['name'] if track['artists'] else '',
                                track
                            ))
                            seen_ids.add(track['id'])
                except Exception as e:
                    logger.debug(f"Search query failed: {query} - {e}")
                    continue
            
            if not all_candidates:
                return CandidateValidation(
                    is_valid=False,
                    verification_method="spotify_not_found",
                    confidence_score=0.0,
                    confidence_level="low",
                    issues=[f"No Spotify results for '{title}' by '{artist}'"]
                )
            
            # Use NLP fuzzy matching to find best candidate
            candidate_pairs = [(cand_title, cand_artist) for cand_title, cand_artist, _ in all_candidates]
            matches = self.text_processor.fuzzy_match_songs(title, artist, candidate_pairs)
            
            if not matches or matches[0].score < 0.6:  # Minimum threshold
                return CandidateValidation(
                    is_valid=False,
                    verification_method="spotify_no_good_match",
                    confidence_score=matches[0].score if matches else 0.0,
                    confidence_level="low",
                    issues=[f"No good fuzzy match found for '{title}' by '{artist}'"]
                )
            
            # Get the best match
            best_match = matches[0]
            
            # Find corresponding Spotify track
            best_track = None
            for cand_title, cand_artist, track in all_candidates:
                if f"{cand_title} by {cand_artist}" == best_match.matched_text:
                    best_track = track
                    break
            
            if not best_track:
                return CandidateValidation(
                    is_valid=False,
                    verification_method="spotify_track_retrieval_error",
                    confidence_score=best_match.score,
                    confidence_level=best_match.confidence,
                    issues=["Could not retrieve matched Spotify track"]
                )
            
            # Extract exact metadata (EXACT IDENTIFICATION context)
            exact_metadata = self.text_processor.preserve_exact_metadata(best_track)
            
            # Determine verification method
            if best_match.score >= 0.95:
                method = "spotify_exact_match"
                self.stats["exact_matched"] += 1
            else:
                method = "spotify_fuzzy_match"
                self.stats["fuzzy_matched"] += 1
            
            # Check what was corrected
            issues = []
            normalized_input_title = self.text_processor.normalize_for_matching(title, 'title')
            normalized_input_artist = self.text_processor.normalize_for_matching(artist, 'artist')
            normalized_found_title = self.text_processor.normalize_for_matching(exact_metadata['exact_title'], 'title')
            normalized_found_artist = self.text_processor.normalize_for_matching(exact_metadata['exact_artist'], 'artist')
            
            if normalized_input_title.lower() != normalized_found_title.lower():
                issues.append(f"Title matched: '{title}' → '{exact_metadata['exact_title']}'")
            
            if normalized_input_artist.lower() != normalized_found_artist.lower():
                issues.append(f"Artist matched: '{artist}' → '{exact_metadata['exact_artist']}'")
            
            self.stats["spotify_verified"] += 1
            
            return CandidateValidation(
                is_valid=True,
                verified_title=exact_metadata['exact_title'],
                verified_artist=exact_metadata['exact_artist'],
                verification_method=method,
                confidence_score=best_match.score,
                confidence_level=best_match.confidence,
                issues=issues,
                spotify_metadata=exact_metadata
            )
                
        except Exception as e:
            logger.error(f"Spotify NLP verification failed for {title} by {artist}: {e}")
            return CandidateValidation(
                is_valid=False,
                verification_method="spotify_error",
                confidence_score=0.0,
                confidence_level="low",
                issues=[f"Spotify verification error: {str(e)}"]
            )
    
    def validate_candidate_list_nlp(self, candidates: List[Dict[str, Any]], 
                                   verify_external: bool = True, 
                                   verbose: bool = False) -> List[Dict[str, Any]]:
        """
        Validate and clean candidates using NLP techniques
        
        Combines MATCHING (deduplication, normalization) with 
        EXACT IDENTIFICATION (Spotify verification)
        """
        if not candidates:
            return []
        
        self.stats["total_candidates"] += len(candidates)
        
        if verbose:
            print(f"🔍 NLP validation of {len(candidates)} candidates...")
        
        validated_candidates = []
        seen_dedup_keys: Set[str] = set()
        
        for candidate in candidates:
            title = candidate.get('title', '').strip()
            artist = candidate.get('artist', '').strip()
            source = candidate.get('source', 'unknown')
            
            if not title or not artist:
                self.stats["invalid_removed"] += 1
                if verbose:
                    print(f"   ❌ Skipped invalid candidate: {title} by {artist}")
                continue
            
            # MATCHING: Create deduplication key using NLP
            dedup_key = self.text_processor.create_deduplication_key(title, artist)
            
            if dedup_key in seen_dedup_keys:
                self.stats["duplicates_removed"] += 1
                if verbose:
                    print(f"   🔄 Skipped duplicate: {title} by {artist}")
                continue
            
            seen_dedup_keys.add(dedup_key)
            
            # Decide whether to verify with Spotify
            should_verify = (
                verify_external and 
                'external' in source and
                self.spotify is not None
            )
            
            if should_verify:
                # MATCHING + EXACT IDENTIFICATION: Verify with Spotify
                validation = self.verify_with_spotify_nlp(title, artist)
                
                if validation.is_valid:
                    # Use exact Spotify metadata
                    final_title = validation.verified_title
                    final_artist = validation.verified_artist
                    
                    # Calculate confidence penalty for corrections
                    confidence_penalty = max(0.0, (1.0 - validation.confidence_score) * 0.3)
                    original_confidence = candidate.get('confidence', 0.7)
                    adjusted_confidence = max(0.1, original_confidence - confidence_penalty)
                    
                    validated_candidates.append({
                        **candidate,
                        'title': final_title,
                        'artist': final_artist,
                        'confidence': adjusted_confidence,
                        'verification': validation.verification_method,
                        'verification_score': validation.confidence_score,
                        'verification_issues': validation.issues,
                        'spotify_metadata': validation.spotify_metadata
                    })
                    
                    if verbose:
                        print(f"   ✅ Verified: {final_title} by {final_artist} (score: {validation.confidence_score:.3f})")
                        for issue in validation.issues:
                            print(f"     ℹ️  {issue}")
                else:
                    # Invalid - skip this candidate
                    self.stats["invalid_removed"] += 1
                    if verbose:
                        print(f"   ❌ Removed invalid: {title} by {artist}")
                        for issue in validation.issues:
                            print(f"     ⚠️  {issue}")
            else:
                # MATCHING only: Just normalize without Spotify verification
                normalized_title = self.text_processor.normalize_for_matching(title, 'title')
                normalized_artist = self.text_processor.normalize_for_matching(artist, 'artist')
                
                validated_candidates.append({
                    **candidate,
                    'title': normalized_title,
                    'artist': normalized_artist,
                    'verification': 'normalized_only'
                })
        
        if verbose:
            print(f"   ✅ NLP validated {len(validated_candidates)}/{len(candidates)} candidates")
        
        return validated_candidates
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return self.stats.copy()


def main():
    """Test the NLP-based verification system"""
    logging.basicConfig(level=logging.INFO)
    
    verifier = NLPCandidateVerifier()
    
    # Test cases including the problematic "It's Raining Tacos"
    test_candidates = [
        {"title": "It's Raining Tacos", "artist": "Parry Gripp", "source": "llm_knowledge_external", "confidence": 0.8},
        {"title": "Banana Pancakes", "artist": "Jack Johnson", "source": "llm_knowledge_external", "confidence": 0.9},
        {"title": "November Rain", "artist": "Guns N' Roses", "source": "database", "confidence": 1.0},
        {"title": "November Rain (Remastered)", "artist": "Guns N' Roses", "source": "llm_knowledge_external", "confidence": 0.7},  # Should dedupe
        {"title": "Jambalaya (On the Bayou)", "artist": "Hank Williams", "source": "llm_knowledge_external", "confidence": 0.8},
        {"title": "Yesterday", "artist": "The Beatles", "source": "database", "confidence": 1.0},  # Should not verify
    ]
    
    print("🎵 Testing NLP-based Candidate Verification")
    print("=" * 60)
    
    validated = verifier.validate_candidate_list_nlp(test_candidates, verify_external=True, verbose=True)
    
    print(f"\n📊 Results:")
    print(f"Original candidates: {len(test_candidates)}")
    print(f"Validated candidates: {len(validated)}")
    
    print(f"\nValid candidates:")
    for i, candidate in enumerate(validated, 1):
        verification = candidate.get('verification', 'unknown')
        confidence = candidate.get('confidence', 0.0)
        score = candidate.get('verification_score', 0.0)
        
        print(f"  {i}. '{candidate['title']}' by '{candidate['artist']}'")
        print(f"     Verification: {verification}")
        print(f"     Confidence: {confidence:.3f}")
        if score > 0:
            print(f"     Match Score: {score:.3f}")
        
        if candidate.get('spotify_metadata'):
            metadata = candidate['spotify_metadata']
            print(f"     Spotify ID: {metadata.get('spotify_id', 'N/A')}")
    
    # Show statistics
    stats = verifier.get_statistics()
    print(f"\n📈 Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    main()
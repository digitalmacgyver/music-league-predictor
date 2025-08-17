#!/usr/bin/env ./venv/bin/python3
"""
Candidate Verification System

Validates song candidates to prevent hallucinations and ensure quality:
- Spotify verification for LLM suggestions
- Title/artist normalization and deduplication
- Data source validation and tracking
"""

import os
import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class CandidateValidation:
    """Result of candidate verification"""
    is_valid: bool
    verified_title: Optional[str] = None
    verified_artist: Optional[str] = None
    verification_method: str = "unverified"
    confidence_penalty: float = 0.0
    issues: List[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []

class CandidateVerifier:
    """Validates and cleans song candidates"""
    
    def __init__(self):
        self.spotify = None
        self.stats = {
            "total_candidates": 0,
            "spotify_verified": 0,
            "spotify_corrected": 0,
            "duplicates_removed": 0,
            "invalid_removed": 0
        }
        
        # Initialize Spotify client for verification
        if os.getenv('SPOTIFY_CLIENT_ID') and os.getenv('SPOTIFY_CLIENT_SECRET'):
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                logger.info("Spotify verification initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify client: {e}")
        else:
            logger.warning("Spotify credentials not found - verification limited")
    
    def normalize_title(self, title: str) -> str:
        """Normalize song title for comparison"""
        if not title:
            return ""
        
        # Remove surrounding quotes (all quote types)
        title = re.sub(r'^["\'""`''""„‚]+|["\'""`''""„‚]+$', '', title.strip())
        
        # Remove common prefixes/suffixes (expanded list)
        suffixes_pattern = r'\s*[-\(\[]?\s*(remaster|remastered|live|remix|acoustic|demo|single version|radio edit|explicit|deluxe|extended|instrumental|karaoke|clean|dirty|uncensored|album version|single|ep version|bonus track|\d{4}\s*remaster|\d{4}|stereo|mono).*?[\)\]]?$'
        title = re.sub(suffixes_pattern, '', title, flags=re.IGNORECASE)
        
        # Standardize punctuation
        title = re.sub(r'\s*[&]\s*', ' & ', title)  # Standardize ampersands
        title = re.sub(r'\s*[+]\s*', ' + ', title)  # Standardize plus signs
        
        # Clean whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def normalize_artist(self, artist: str) -> str:
        """Normalize artist name for comparison"""
        if not artist:
            return ""
        
        # Remove surrounding quotes
        artist = re.sub(r'^["\'""]|["\'""]$', '', artist.strip())
        
        # Standardize featuring patterns
        artist = re.sub(r'\s*(ft\.|feat\.|featuring|ft|feat)\s+', ' feat. ', artist, flags=re.IGNORECASE)
        
        # Standardize 'and' vs '&'
        artist = re.sub(r'\s+and\s+', ' & ', artist, flags=re.IGNORECASE)
        
        # Clean whitespace
        artist = re.sub(r'\s+', ' ', artist).strip()
        
        return artist
    
    def create_dedup_key(self, title: str, artist: str) -> str:
        """Create a key for deduplication"""
        norm_title = self.normalize_title(title).lower()
        norm_artist = self.normalize_artist(artist).lower()
        return f"{norm_title}|{norm_artist}"
    
    def verify_with_spotify(self, title: str, artist: str) -> CandidateValidation:
        """Verify song exists on Spotify and get correct metadata"""
        
        if not self.spotify:
            return CandidateValidation(
                is_valid=False,
                verification_method="no_spotify",
                confidence_penalty=0.3,
                issues=["Spotify verification unavailable"]
            )
        
        try:
            # Try exact search first
            query = f'track:"{title}" artist:"{artist}"'
            exact_results = self.spotify.search(q=query, type='track', limit=5)
            
            # Try looser search regardless (we'll check both sets of results)
            query = f'{title} {artist}'
            loose_results = self.spotify.search(q=query, type='track', limit=10)
            
            # Combine results, prioritizing exact search results
            all_tracks = []
            if exact_results['tracks']['items']:
                all_tracks.extend(exact_results['tracks']['items'])
            if loose_results['tracks']['items']:
                # Add loose results that aren't already in exact results
                exact_ids = {track['id'] for track in exact_results['tracks']['items']}
                all_tracks.extend([track for track in loose_results['tracks']['items'] 
                                 if track['id'] not in exact_ids])
            
            # Create a results structure matching expected format
            results = {'tracks': {'items': all_tracks}}
            
            if not results['tracks']['items']:
                return CandidateValidation(
                    is_valid=False,
                    verification_method="spotify_not_found",
                    confidence_penalty=0.8,
                    issues=[f"Song not found on Spotify: '{title}' by '{artist}'"]
                )
            
            # Find best match
            best_match = None
            best_score = 0
            
            norm_title = self.normalize_title(title).lower()
            norm_artist = self.normalize_artist(artist).lower()
            
            for track in results['tracks']['items']:
                if not track or not track.get('name') or not track.get('artists'):
                    continue
                
                track_title = self.normalize_title(track['name']).lower()
                track_artist = self.normalize_artist(track['artists'][0]['name']).lower()
                
                # Calculate similarity score - much stricter matching
                # Only accept exact matches or very close matches (not just substrings)
                title_match = 1.0 if track_title == norm_title else 0.0
                
                # For title, allow some flexibility for remastered versions, common prefixes, etc.
                if title_match == 0.0:
                    # Check if one is a subset with common suffixes/prefixes
                    if (norm_title in track_title and 
                        any(suffix in track_title for suffix in [' - remastered', ' - live', ' - remix', ' (remastered', ' (live'])):
                        title_match = 0.9
                    elif (track_title in norm_title and len(track_title) >= len(norm_title) * 0.8):
                        title_match = 0.8
                    # Handle common title variations (missing/extra prefixes)
                    else:
                        # Remove common prefixes and try again
                        common_prefixes = ["it's ", "its ", "the ", "a ", "an "]
                        title_no_prefix = norm_title
                        track_no_prefix = track_title
                        
                        for prefix in common_prefixes:
                            if title_no_prefix.startswith(prefix):
                                title_no_prefix = title_no_prefix[len(prefix):]
                            if track_no_prefix.startswith(prefix):
                                track_no_prefix = track_no_prefix[len(prefix):]
                        
                        # Check if they match without prefixes
                        if title_no_prefix == track_no_prefix and len(title_no_prefix) > 3:
                            title_match = 0.85  # High confidence for prefix-only differences
                
                # Artist matching - be strict, no substring matching unless very close
                artist_match = 1.0 if track_artist == norm_artist else 0.0
                
                if artist_match == 0.0:
                    # Only allow artist corrections for obvious variations
                    if (len(norm_artist) > 3 and len(track_artist) > 3 and
                        (norm_artist in track_artist or track_artist in norm_artist) and
                        abs(len(norm_artist) - len(track_artist)) <= 5):
                        artist_match = 0.7
                
                # Require high confidence - both title and artist must be very close
                score = (title_match * 0.7 + artist_match * 0.3)  # Weight title more heavily
                
                if score > best_score and score >= 0.8:  # Much higher threshold
                    best_score = score
                    best_match = track
            
            if best_match:
                verified_title = best_match['name']
                verified_artist = best_match['artists'][0]['name']
                
                # Check if we corrected anything
                title_corrected = self.normalize_title(verified_title) != self.normalize_title(title)
                artist_corrected = self.normalize_artist(verified_artist) != self.normalize_artist(artist)
                
                issues = []
                confidence_penalty = 0.0
                
                if title_corrected:
                    issues.append(f"Title corrected: '{title}' → '{verified_title}'")
                    confidence_penalty += 0.1
                
                if artist_corrected:
                    issues.append(f"Artist corrected: '{artist}' → '{verified_artist}'")
                    confidence_penalty += 0.1
                
                method = "spotify_corrected" if issues else "spotify_verified"
                
                return CandidateValidation(
                    is_valid=True,
                    verified_title=verified_title,
                    verified_artist=verified_artist,
                    verification_method=method,
                    confidence_penalty=confidence_penalty,
                    issues=issues
                )
            else:
                return CandidateValidation(
                    is_valid=False,
                    verification_method="spotify_no_match",
                    confidence_penalty=0.7,
                    issues=[f"No good Spotify match found for '{title}' by '{artist}'"]
                )
                
        except Exception as e:
            logger.error(f"Spotify verification failed for {title} by {artist}: {e}")
            return CandidateValidation(
                is_valid=False,
                verification_method="spotify_error",
                confidence_penalty=0.5,
                issues=[f"Spotify verification error: {str(e)}"]
            )
    
    def validate_candidate_list(self, candidates: List[Dict[str, Any]], 
                              verify_external: bool = True, 
                              verbose: bool = False) -> List[Dict[str, Any]]:
        """Validate and clean a list of candidates"""
        
        if not candidates:
            return []
        
        self.stats["total_candidates"] += len(candidates)
        
        if verbose:
            print(f"🔍 Validating {len(candidates)} candidates...")
        
        validated_candidates = []
        seen_keys: Set[str] = set()
        
        for candidate in candidates:
            title = candidate.get('title', '').strip()
            artist = candidate.get('artist', '').strip()
            source = candidate.get('source', 'unknown')
            
            if not title or not artist:
                self.stats["invalid_removed"] += 1
                if verbose:
                    print(f"   ❌ Skipped invalid candidate: {title} by {artist}")
                continue
            
            # Create deduplication key
            dedup_key = self.create_dedup_key(title, artist)
            
            if dedup_key in seen_keys:
                self.stats["duplicates_removed"] += 1
                if verbose:
                    print(f"   🔄 Skipped duplicate: {title} by {artist}")
                continue
            
            seen_keys.add(dedup_key)
            
            # Decide whether to verify
            should_verify = (
                verify_external and 
                'external' in source and
                self.spotify is not None
            )
            
            if should_verify:
                validation = self.verify_with_spotify(title, artist)
                
                if validation.is_valid:
                    # Use verified/corrected metadata
                    final_title = validation.verified_title or title
                    final_artist = validation.verified_artist or artist
                    
                    # Apply confidence penalty
                    original_confidence = candidate.get('confidence', 0.7)
                    adjusted_confidence = max(0.1, original_confidence - validation.confidence_penalty)
                    
                    validated_candidates.append({
                        **candidate,
                        'title': final_title,
                        'artist': final_artist,
                        'confidence': adjusted_confidence,
                        'verification': validation.verification_method,
                        'verification_issues': validation.issues
                    })
                    
                    if validation.verification_method == "spotify_verified":
                        self.stats["spotify_verified"] += 1
                    elif validation.verification_method == "spotify_corrected":
                        self.stats["spotify_corrected"] += 1
                        if verbose:
                            print(f"   ✅ Verified & corrected: {final_title} by {final_artist}")
                    
                    if verbose and validation.issues:
                        for issue in validation.issues:
                            print(f"     ⚠️  {issue}")
                else:
                    # Invalid - skip this candidate
                    self.stats["invalid_removed"] += 1
                    if verbose:
                        print(f"   ❌ Removed invalid: {title} by {artist}")
                        for issue in validation.issues:
                            print(f"     ⚠️  {issue}")
            else:
                # No verification needed - just normalize
                normalized_title = self.normalize_title(title)
                normalized_artist = self.normalize_artist(artist)
                
                validated_candidates.append({
                    **candidate,
                    'title': normalized_title,
                    'artist': normalized_artist,
                    'verification': 'normalized_only'
                })
        
        if verbose:
            print(f"   ✅ Validated {len(validated_candidates)}/{len(candidates)} candidates")
        
        return validated_candidates
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return self.stats.copy()

def main():
    """Test the verification system"""
    
    logging.basicConfig(level=logging.INFO)
    
    verifier = CandidateVerifier()
    
    # Test cases with known issues
    test_candidates = [
        {"title": "Banana Pancakes", "artist": "Jack Johnson", "source": "llm_knowledge_external"},
        {"title": "\"Banana Pancakes\"", "artist": "Jack Johnson", "source": "llm_knowledge_external"},  # Duplicate with quotes
        {"title": "Rice & Beans", "artist": "Blue Scholars", "source": "llm_knowledge_external"},  # Likely hallucination
        {"title": "Rice & Beans", "artist": "Lizzo", "source": "llm_knowledge_external"},  # Likely hallucination
        {"title": "Hot Tamales", "artist": "Junior Wells", "source": "llm_knowledge_external"},  # Likely hallucination
        {"title": "TV Dinner", "artist": "ZZ Top", "source": "llm_knowledge_external"},  # Should be "TV Dinners"
        {"title": "Yesterday", "artist": "The Beatles", "source": "database"},  # Valid, should not verify
    ]
    
    print("🔍 Testing Candidate Verification System")
    print("=" * 60)
    
    validated = verifier.validate_candidate_list(test_candidates, verify_external=True, verbose=True)
    
    print(f"\n📊 Results:")
    print(f"Original candidates: {len(test_candidates)}")
    print(f"Validated candidates: {len(validated)}")
    
    print(f"\nValid candidates:")
    for i, candidate in enumerate(validated, 1):
        verification = candidate.get('verification', 'unknown')
        confidence = candidate.get('confidence', 0.0)
        print(f"  {i}. {candidate['title']} by {candidate['artist']}")
        print(f"     Verification: {verification}, Confidence: {confidence:.2f}")
    
    # Show statistics
    stats = verifier.get_statistics()
    print(f"\n📈 Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    main()
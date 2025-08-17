#!/usr/bin/env ./venv/bin/python3
"""
Test the NLP verification system with the original problematic cases
"""

from candidate_verification_nlp import NLPCandidateVerifier

def test_original_issues():
    """Test the exact cases that were failing before"""
    print("🎵 Testing Original Verification Issues")
    print("=" * 50)
    
    verifier = NLPCandidateVerifier()
    
    # Test the specific cases mentioned in the original request
    test_cases = [
        ("It's Raining Tacos", "Parry Gripp"),
        ("Jambalaya (On the Bayou)", "Hank Williams"),
        ("Sugar Sugar Sugar", "ESG")  # This should fail (doesn't exist)
    ]
    
    for title, artist in test_cases:
        print(f"\nTesting: '{title}' by {artist}")
        print("-" * 40)
        
        validation = verifier.verify_with_spotify_nlp(title, artist)
        
        if validation.is_valid:
            print(f"✅ FOUND: '{validation.verified_title}' by '{validation.verified_artist}'")
            print(f"   Method: {validation.verification_method}")
            print(f"   Confidence: {validation.confidence_score:.3f} ({validation.confidence_level})")
            print(f"   Spotify ID: {validation.spotify_metadata['spotify_id']}")
            
            if validation.issues:
                print("   Corrections made:")
                for issue in validation.issues:
                    print(f"     • {issue}")
        else:
            print(f"❌ NOT FOUND")
            print(f"   Method: {validation.verification_method}")
            print(f"   Issues:")
            for issue in validation.issues:
                print(f"     • {issue}")

if __name__ == "__main__":
    test_original_issues()
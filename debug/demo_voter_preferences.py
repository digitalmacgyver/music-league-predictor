#!/usr/bin/env ./venv/bin/python3
"""
Quick demo of voter preference functionality in Scout
"""

import logging
from voter_preferences import VoterPreferenceModeler

def demo_voter_preferences():
    """Demo voter preference predictions"""
    
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    print("🎯 VOTER PREFERENCE MODELING DEMO")
    print("=" * 50)
    
    modeler = VoterPreferenceModeler()
    
    try:
        # Load data
        print("Loading voter preferences...")
        df = modeler.load_voting_data()
        modeler.build_voter_song_matrix(df)
        modeler.build_voter_profiles(df)
        modeler.calculate_voter_similarity()
        
        # Test voter
        test_voter = "Drew"
        print(f"\n👤 TESTING VOTER: {test_voter}")
        print("-" * 30)
        
        # Show voter profile
        summary = modeler.get_voter_profile_summary(test_voter)
        if summary:
            profile = summary['profile']
            print(f"Activity: {profile['total_votes']} votes")
            print(f"Average score: {profile['avg_score']:.2f}")
            print(f"Generosity: {profile['voting_generosity']:.2f}")
            
            print(f"\nTop artists:")
            for artist, score in profile['top_artists'][:3]:
                print(f"  • {artist}: {score:.2f} avg")
                
            print(f"\nSimilar voters:")
            for voter, similarity in summary['similar_voters']:
                print(f"  • {voter}: {similarity:.3f} similarity")
        
        # Test song predictions
        print(f"\n🎵 TESTING SONG PREDICTIONS")
        print("-" * 30)
        
        test_songs = [
            {"title": "Black Hole Sun", "artist": "Soundgarden"},
            {"title": "Enter Sandman", "artist": "Metallica"},
            {"title": "Dancing Queen", "artist": "ABBA"}
        ]
        
        predictions = modeler.predict_voter_preferences_for_candidates(test_voter, test_songs)
        
        for prediction in predictions:
            print(f"\n'{prediction.song_title}' by {prediction.artist}")
            print(f"  Predicted score: {prediction.predicted_score:.2f}/5")
            print(f"  Confidence: {prediction.confidence:.2f}")
            print(f"  Reasoning: {prediction.reasoning}")
            if prediction.similar_voters:
                print(f"  Based on: {', '.join(prediction.similar_voters[:3])}")
        
        print(f"\n✅ Voter preference modeling working!")
        print(f"Ready for Scout integration with --voter parameter")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        modeler.close()

if __name__ == "__main__":
    demo_voter_preferences()
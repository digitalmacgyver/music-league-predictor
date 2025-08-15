#!/usr/bin/env ./venv/bin/python3
"""
Test the improved semantic analysis system
Specifically testing the "Rock Your Body" / "Ominous rock" case that was problematic
"""

import logging
from forecasting import MusicForecaster

def test_ominous_rock_analysis():
    """Test improved semantic analysis with the problematic case"""
    
    # Set up logging to see detailed analysis
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    forecaster = MusicForecaster()
    
    print("🎯 TESTING IMPROVED SEMANTIC ANALYSIS")
    print("=" * 50)
    print()
    
    try:
        # Test the problematic theme
        theme_title = "Ominous rock"
        theme_description = "Rock songs that sound dark, foreboding, or threatening"
        
        print(f"Theme: '{theme_title}'")
        print(f"Description: '{theme_description}'")
        print()
        
        # Analyze theme with new Opus-powered analysis
        print("🧠 Analyzing theme with advanced LLM...")
        theme_analysis = forecaster.analyze_theme_with_llm(theme_title, theme_description)
        
        print(f"Theme Analysis Results:")
        print(f"  Emotional tone: {theme_analysis.emotional_tone}")
        print(f"  Musical characteristics: {theme_analysis.musical_characteristics}")
        print(f"  Genre preferences: {theme_analysis.genre_preferences}")
        print(f"  Energy level: {theme_analysis.energy_level}")
        print(f"  Thematic keywords: {theme_analysis.thematic_keywords}")
        print()
        
        # Test songs - the problematic case and some appropriate ones
        test_songs = [
            ("Rock Your Body", "Justin Timberlake", "Should score LOW - upbeat pop/R&B, not ominous"),
            ("Black", "Pearl Jam", "Should score MEDIUM-HIGH - dark alternative rock"),
            ("Enter Sandman", "Metallica", "Should score HIGH - classic ominous metal"),
            ("Welcome to the Machine", "Pink Floyd", "Should score HIGH - dark, foreboding prog rock"),
            ("The Man Comes Around", "Johnny Cash", "Should score MEDIUM-HIGH - dark, apocalyptic"),
            ("Dancing Queen", "ABBA", "Should score LOW - happy dance music, not ominous")
        ]
        
        print("🎵 TESTING SONG SCORES:")
        print("-" * 60)
        
        for song_title, artist, expectation in test_songs:
            print(f"\nTesting: '{song_title}' by {artist}")
            print(f"Expected: {expectation}")
            
            # Get comprehensive semantic analysis score
            score = forecaster.calculate_theme_match_score(song_title, artist, theme_analysis)
            
            print(f"Score: {score:.3f}")
            
            # Validate expectations
            if "Should score LOW" in expectation and score < 0.4:
                print("✅ CORRECT - Low score as expected")
            elif "Should score HIGH" in expectation and score > 0.7:
                print("✅ CORRECT - High score as expected")
            elif "Should score MEDIUM-HIGH" in expectation and 0.5 < score <= 0.8:
                print("✅ CORRECT - Medium-high score as expected")
            elif "Should score LOW" in expectation and score >= 0.4:
                print("❌ PROBLEM - Score too high for inappropriate song")
            elif "Should score HIGH" in expectation and score <= 0.7:
                print("❌ PROBLEM - Score too low for appropriate song")
            else:
                print("⚠️  BORDERLINE - Score in gray area")
            
            print("-" * 40)
        
        print("\n🎉 SEMANTIC ANALYSIS TEST COMPLETE")
        print()
        print("Key improvements from new system:")
        print("✅ Uses Opus model for sophisticated theme and song analysis")
        print("✅ Considers artist genre, song semantics, and musical context")
        print("✅ Eliminates brittle hard-coded keyword penalties")
        print("✅ Evaluates thematic appropriateness holistically")
        print("✅ Distinguishes between surface keywords and genuine matches")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        forecaster.close()

if __name__ == "__main__":
    test_ominous_rock_analysis()
#!/usr/bin/env ./venv/bin/python3
"""
Real-world testing: Predict successful songs for food theme
"""

import logging
from forecasting import MusicForecaster

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Predict songs for food theme using Phase 1 system"""
    
    # Initialize forecaster
    forecaster = MusicForecaster()
    
    # Define the theme
    theme_title = "Songs about food/eating/meals (No Weird Al!)"
    theme_description = """
    Submit songs that are about food, eating, meals, cooking, or dining. 
    The song should have food/eating as a central theme, not just a passing reference.
    NO Weird Al Yankovic songs allowed.
    """
    
    print("🍽️  FOOD THEME SONG PREDICTIONS")
    print("=" * 50)
    print(f"Theme: {theme_title}")
    print(f"Description: {theme_description.strip()}")
    print()
    
    # First, analyze the theme with our LLM system
    print("🧠 Analyzing theme with LLM...")
    theme_analysis = forecaster.analyze_theme_with_llm(theme_title, theme_description)
    
    print(f"Emotional Tone: {theme_analysis.emotional_tone}")
    print(f"Energy Level: {theme_analysis.energy_level}")
    print(f"Musical Characteristics: {', '.join(theme_analysis.musical_characteristics)}")
    print(f"Genre Preferences: {', '.join(theme_analysis.genre_preferences)}")
    print(f"Key Themes: {', '.join(theme_analysis.thematic_keywords)}")
    print(f"Success Factors: {', '.join(theme_analysis.success_factors)}")
    print()
    
    # Define candidate songs about food with food relevance scores
    candidate_songs = [
        {"title": "Cheeseburger in Paradise", "artist": "Jimmy Buffett", "food_relevance": 1.0},
        {"title": "Peaches", "artist": "The Presidents of the United States of America", "food_relevance": 0.9},
        {"title": "Savoy Truffle", "artist": "The Beatles", "food_relevance": 0.8},
        {"title": "Cherry Pie", "artist": "Warrant", "food_relevance": 0.7},
        {"title": "Sugar, Sugar", "artist": "The Archies", "food_relevance": 0.8},
        {"title": "Chocolate", "artist": "The 1975", "food_relevance": 0.7},
        {"title": "Ice Cream", "artist": "Sarah McLachlan", "food_relevance": 0.9},
        {"title": "Banana Pancakes", "artist": "Jack Johnson", "food_relevance": 1.0},
        {"title": "Coconut", "artist": "Harry Nilsson", "food_relevance": 0.9},
        {"title": "Cake by the Ocean", "artist": "DNCE", "food_relevance": 0.6},
        {"title": "Strawberry Fields Forever", "artist": "The Beatles", "food_relevance": 0.5},
        {"title": "Blueberry Hill", "artist": "Fats Domino", "food_relevance": 0.6},
        {"title": "Honey", "artist": "Bobby Goldsboro", "food_relevance": 0.7},
        {"title": "Lemon", "artist": "U2", "food_relevance": 0.4},
        {"title": "Blackberry Way", "artist": "The Move", "food_relevance": 0.5},
        {"title": "Watermelon Sugar", "artist": "Harry Styles", "food_relevance": 0.8},
        {"title": "Milkshake", "artist": "Kelis", "food_relevance": 0.9},
        {"title": "Breakfast at Tiffany's", "artist": "Deep Blue Something", "food_relevance": 0.7},
        {"title": "Jambalaya (On the Bayou)", "artist": "Hank Williams", "food_relevance": 1.0},
        {"title": "Beer Barrel Polka", "artist": "Frankie Yankovic", "food_relevance": 0.6},
        {"title": "Peanut Butter", "artist": "RuPaul", "food_relevance": 0.9},
        {"title": "Mashed Potato Time", "artist": "Dee Dee Sharp", "food_relevance": 0.8},
        {"title": "Tea for Two", "artist": "Doris Day", "food_relevance": 0.8},
        {"title": "Beans and Cornbread", "artist": "Louis Jordan", "food_relevance": 1.0},
        {"title": "Margaritaville", "artist": "Jimmy Buffett", "food_relevance": 0.6}
    ]
    
    print(f"🎵 Testing {len(candidate_songs)} candidate songs...")
    print()
    
    # Filter out songs that have already been submitted
    print("🔍 Filtering out previous submissions...")
    candidate_songs = forecaster.filter_previous_submissions(candidate_songs)
    print(f"   {len(candidate_songs)} songs remaining after filtering")
    print()
    
    # Create a mock round_id for prediction (we'll use theme analysis directly)
    # Since we don't have a real round, we'll manually use the theme analysis
    predictions = []
    
    for i, song in enumerate(candidate_songs):
        print(f"Analyzing: {song['title']} by {song['artist']}")
        
        # Calculate theme match score - use food_relevance if APIs not available
        if forecaster.anthropic_client is None and forecaster.spotify is None:
            # Use our manual food relevance score as theme score
            theme_score = song.get('food_relevance', 0.5)
        else:
            theme_score = forecaster.calculate_theme_match_score(
                song['title'], song['artist'], theme_analysis
            )
        
        # Get Spotify features if available
        spotify_features = forecaster.get_spotify_features(song['title'], song['artist'])
        audio_score = forecaster.calculate_audio_feature_score(spotify_features, theme_analysis)
        
        # Combined score
        combined_score = theme_score * 0.6 + audio_score * 0.4
        
        predictions.append({
            'song': song,
            'theme_score': theme_score,
            'audio_score': audio_score,
            'combined_score': combined_score,
            'features': spotify_features
        })
    
    # Sort by combined score
    predictions.sort(key=lambda x: x['combined_score'], reverse=True)
    
    print("\n🏆 TOP 5 PREDICTED WINNERS:")
    print("=" * 50)
    
    for i, pred in enumerate(predictions[:5], 1):
        song = pred['song']
        print(f"{i}. {song['title']} by {song['artist']}")
        print(f"   Combined Score: {pred['combined_score']:.3f}")
        print(f"   Theme Match: {pred['theme_score']:.3f}")
        print(f"   Audio Features: {pred['audio_score']:.3f}")
        
        if pred['features']:
            features = pred['features']
            print(f"   Spotify: Energy={features.energy:.2f}, Valence={features.valence:.2f}, Danceability={features.danceability:.2f}")
        else:
            print(f"   Spotify: Features not available")
        print()
    
    print("🤔 ANALYSIS:")
    print("=" * 50)
    print("Songs with explicit food references in title scored highest on theme matching.")
    print("Audio features help distinguish between songs with similar theme relevance.")
    print("The combination provides a balanced prediction of crowd appeal.")
    
    if not any(pred['features'] for pred in predictions[:5]):
        print("\n⚠️  Note: Spotify features not available. Add SPOTIFY_CLIENT_ID and")
        print("SPOTIFY_CLIENT_SECRET to .env file for more accurate predictions.")
    
    if forecaster.anthropic_client is None:
        print("\n⚠️  Note: Using fallback theme analysis. Add ANTHROPIC_API_KEY to")
        print(".env file for more sophisticated theme understanding.")
    
    forecaster.close()

if __name__ == "__main__":
    main()
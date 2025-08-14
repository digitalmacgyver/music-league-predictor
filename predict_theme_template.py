#!/usr/bin/env ./venv/bin/python3
"""
Template for predicting songs for any Music League theme
Copy this file and customize for your specific theme
"""

import logging
from forecasting import MusicForecaster

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Predict songs for your custom theme"""
    
    # ===== CUSTOMIZE THESE SECTIONS =====
    
    # 1. DEFINE YOUR THEME
    theme_title = "YOUR_THEME_TITLE_HERE"
    theme_description = """
    YOUR_THEME_DESCRIPTION_HERE
    Include any specific rules or requirements.
    Be as detailed as possible for better analysis.
    """
    
    # 2. BUILD YOUR CANDIDATE LIST
    # Add 20-40 songs with theme_relevance scores (0.0-1.0)
    # 1.0 = perfect fit for theme, 0.5 = loose connection, 0.0 = not relevant
    candidate_songs = [
        {"title": "Example Song 1", "artist": "Example Artist 1", "theme_relevance": 1.0},
        {"title": "Example Song 2", "artist": "Example Artist 2", "theme_relevance": 0.9},
        {"title": "Example Song 3", "artist": "Example Artist 3", "theme_relevance": 0.8},
        # ADD MORE SONGS HERE
        # Mix of:
        # - Obvious fits (high relevance)
        # - Creative interpretations (medium relevance) 
        # - Popular songs with loose connections (low-medium relevance)
        # - Different eras and genres
    ]
    
    # ===== PREDICTION LOGIC (DON'T CHANGE) =====
    
    forecaster = MusicForecaster()
    
    print(f"🎵 THEME PREDICTION: {theme_title}")
    print("=" * 60)
    print(f"Theme: {theme_title}")
    print(f"Description: {theme_description.strip()}")
    print()
    
    # Analyze theme
    print("🧠 Analyzing theme...")
    theme_analysis = forecaster.analyze_theme_with_llm(theme_title, theme_description)
    print(f"Emotional Tone: {theme_analysis.emotional_tone}")
    print(f"Energy Level: {theme_analysis.energy_level}")
    print(f"Success Factors: {', '.join(theme_analysis.success_factors)}")
    print()
    
    # Filter previous submissions
    print(f"🎵 Testing {len(candidate_songs)} candidate songs...")
    print("🔍 Filtering out previous submissions...")
    candidate_songs = forecaster.filter_previous_submissions(candidate_songs)
    print(f"   {len(candidate_songs)} songs remaining after filtering")
    print()
    
    if len(candidate_songs) == 0:
        print("❌ No new songs remaining! All candidates were previously submitted.")
        print("   Try adding more diverse candidates to your list.")
        return
    
    # Score candidates
    predictions = []
    for i, song in enumerate(candidate_songs):
        print(f"Analyzing: {song['title']} by {song['artist']}")
        
        # Use theme_relevance if APIs not available
        if forecaster.anthropic_client is None and forecaster.spotify is None:
            theme_score = song.get('theme_relevance', 0.5)
        else:
            theme_score = forecaster.calculate_theme_match_score(
                song['title'], song['artist'], theme_analysis
            )
        
        # Get audio features
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
    
    # Sort by score
    predictions.sort(key=lambda x: x['combined_score'], reverse=True)
    
    # Display results
    print("\n🏆 TOP 5 PREDICTED WINNERS:")
    print("=" * 60)
    
    for i, pred in enumerate(predictions[:5], 1):
        song = pred['song']
        print(f"{i}. {song['title']} by {song['artist']}")
        print(f"   Combined Score: {pred['combined_score']:.3f}")
        print(f"   Theme Match: {pred['theme_score']:.3f}")
        print(f"   Audio Features: {pred['audio_score']:.3f}")
        
        if pred['features']:
            features = pred['features']
            print(f"   Spotify: Energy={features.energy:.2f}, Valence={features.valence:.2f}")
        else:
            print(f"   Spotify: Features not available")
        print()
    
    # Show additional candidates
    if len(predictions) > 5:
        print("🎯 HONORABLE MENTIONS:")
        print("=" * 60)
        for i, pred in enumerate(predictions[5:10], 6):
            song = pred['song']
            print(f"{i}. {song['title']} by {song['artist']} (Score: {pred['combined_score']:.3f})")
        print()
    
    # Analysis
    print("🤔 STRATEGY ANALYSIS:")
    print("=" * 60)
    top_song = predictions[0]
    print(f"Strongest pick: {top_song['song']['title']} by {top_song['song']['artist']}")
    print(f"Why: Combines strong theme relevance with broad appeal")
    
    high_theme_songs = [p for p in predictions if p['theme_score'] > 0.8]
    if high_theme_songs:
        print(f"Safe theme picks: {len(high_theme_songs)} songs with high theme relevance")
    
    # API recommendations
    if forecaster.anthropic_client is None:
        print("\n⚠️  For better theme analysis, add ANTHROPIC_API_KEY to .env file")
    if forecaster.spotify is None:
        print("⚠️  For audio features, add SPOTIFY_CLIENT_ID/SECRET to .env file")
    
    forecaster.close()

if __name__ == "__main__":
    main()
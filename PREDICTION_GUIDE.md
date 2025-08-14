# Music League Theme Prediction Guide

## Step-by-Step Instructions for Predicting Songs for Any Theme

### Prerequisites

1. **Ensure database is up to date:**
   ```bash
   ./venv/bin/python3 scraper.py clean
   ```

2. **Optional: Set up API keys for enhanced predictions:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # ANTHROPIC_API_KEY=your_key_here
   # SPOTIFY_CLIENT_ID=your_key_here  
   # SPOTIFY_CLIENT_SECRET=your_key_here
   ```

### Method 1: Quick Prediction with Template Script

1. **Copy the food theme template:**
   ```bash
   cp predict_food_theme.py predict_[THEME_NAME].py
   ```

2. **Edit the theme details:**
   ```python
   # Update these variables in the script:
   theme_title = "Your Theme Title Here"
   theme_description = """
   Detailed description of the theme requirements.
   Any special rules or restrictions.
   """
   ```

3. **Update candidate songs list:**
   ```python
   candidate_songs = [
       {"title": "Song Title", "artist": "Artist Name", "food_relevance": 0.9},
       # Add 20-30 candidate songs with relevance scores (0.0-1.0)
       # Higher scores = more relevant to theme
   ]
   ```

4. **Run the prediction:**
   ```bash
   ./venv/bin/python3 predict_[THEME_NAME].py
   ```

### Method 2: Using the Core Forecasting System Directly

1. **Create a custom prediction script:**

```python
#!/usr/bin/env ./venv/bin/python3
from forecasting import MusicForecaster

def predict_for_theme(theme_title, theme_description, candidates):
    forecaster = MusicForecaster()
    
    # Filter out previous submissions
    filtered_candidates = forecaster.filter_previous_submissions(candidates)
    print(f"Filtered {len(candidates)} to {len(filtered_candidates)} new songs")
    
    # Analyze theme
    theme_analysis = forecaster.analyze_theme_with_llm(theme_title, theme_description)
    
    # Score candidates
    predictions = []
    for song in filtered_candidates:
        # Use manual relevance score if APIs not available
        if forecaster.anthropic_client is None and forecaster.spotify is None:
            theme_score = song.get('theme_relevance', 0.5)
        else:
            theme_score = forecaster.calculate_theme_match_score(
                song['title'], song['artist'], theme_analysis
            )
        
        # Get audio features
        spotify_features = forecaster.get_spotify_features(song['title'], song['artist'])
        audio_score = forecaster.calculate_audio_feature_score(spotify_features, theme_analysis)
        
        combined_score = theme_score * 0.6 + audio_score * 0.4
        
        predictions.append({
            'song': song,
            'combined_score': combined_score,
            'theme_score': theme_score,
            'audio_score': audio_score
        })
    
    # Sort and return top 5
    predictions.sort(key=lambda x: x['combined_score'], reverse=True)
    return predictions[:5]

# Example usage:
candidates = [
    {"title": "Song A", "artist": "Artist A", "theme_relevance": 0.9},
    {"title": "Song B", "artist": "Artist B", "theme_relevance": 0.7},
    # ... more songs
]

results = predict_for_theme(
    "Theme Title", 
    "Theme description...", 
    candidates
)

for i, pred in enumerate(results, 1):
    song = pred['song']
    print(f"{i}. {song['title']} by {song['artist']} (Score: {pred['combined_score']:.3f})")
```

### Method 3: Interactive Theme Analysis

1. **Analyze theme characteristics first:**
   ```python
   from forecasting import MusicForecaster
   
   forecaster = MusicForecaster()
   analysis = forecaster.analyze_theme_with_llm("Theme", "Description")
   
   print(f"Emotional Tone: {analysis.emotional_tone}")
   print(f"Energy Level: {analysis.energy_level}")
   print(f"Success Factors: {analysis.success_factors}")
   ```

2. **Use insights to build candidate list manually**

3. **Run predictions on refined candidates**

### Step-by-Step Example: "Summer Songs" Theme

1. **Create the script:**
   ```bash
   cp predict_food_theme.py predict_summer_songs.py
   ```

2. **Edit theme details:**
   ```python
   theme_title = "Summer Songs"
   theme_description = "Songs that capture the feeling of summer - whether through lyrics about summer activities, warm weather vibes, or that nostalgic summer feeling."
   ```

3. **Build candidate list:**
   ```python
   candidate_songs = [
       {"title": "Summer Breeze", "artist": "Seals and Crofts", "theme_relevance": 1.0},
       {"title": "Summer of '69", "artist": "Bryan Adams", "theme_relevance": 1.0},
       {"title": "Cruel Summer", "artist": "Bananarama", "theme_relevance": 0.9},
       {"title": "Summertime", "artist": "DJ Jazzy Jeff & The Fresh Prince", "theme_relevance": 1.0},
       {"title": "California Gurls", "artist": "Katy Perry", "theme_relevance": 0.8},
       {"title": "Surfin' USA", "artist": "The Beach Boys", "theme_relevance": 0.9},
       {"title": "Blurred Lines", "artist": "Robin Thicke", "theme_relevance": 0.7},
       {"title": "Vacation", "artist": "The Go-Go's", "theme_relevance": 0.8},
       # Add 15-20 more candidates...
   ]
   ```

4. **Run prediction:**
   ```bash
   ./venv/bin/python3 predict_summer_songs.py
   ```

### Tips for Building Good Candidate Lists

1. **Brainstorm 25-40 songs** initially
2. **Mix obvious and creative picks** (80% obvious, 20% creative)
3. **Include different eras** (60s-present)
4. **Score relevance honestly** (1.0 = perfect fit, 0.5 = loose connection)
5. **Consider voter psychology** - what sounds fun vs. what sounds pretentious

### Interpreting Results

- **Combined Score > 0.8**: Very strong picks
- **Combined Score 0.6-0.8**: Solid choices  
- **Combined Score < 0.6**: Risky picks

The system automatically:
- ✅ Filters out previous submissions
- ✅ Balances theme relevance with musical appeal
- ✅ Provides reasoning for each prediction
- ✅ Works without API keys (though enhanced with them)

### Troubleshooting

**"No songs remaining after filtering"**
- Your candidates were all previously submitted
- Add more diverse candidates to your list

**"All scores are 0.200"**  
- Add `theme_relevance` scores to your candidate songs
- The fallback system needs manual relevance ratings

**"Spotify features not available"**
- Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to .env
- Or continue with audio_score = 0.5 fallback
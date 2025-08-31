# lib/ Directory

This directory contains the core library modules and components used by the Music League applications.

## Core Libraries

### Data & Database
- **config.py** - Project configuration and database paths
- **setup_db.py** - Database schema creation and management

### Music Analysis & Prediction
- **forecasting.py** - Core music scoring and prediction algorithms
- **ensemble_forecasting.py** - Advanced ensemble prediction models
- **ensemble_models.py** - Machine learning model implementations
- **historical_patterns.py** - Historical voting pattern analysis
- **preference_forecaster.py** - Group preference prediction

### NLP & Text Processing
- **nlp_text_processor.py** - Professional NLP text processing system
- **candidate_verification_nlp.py** - NLP-based song verification
- **scout_nlp_integration.py** - Scout integration with NLP features

### Discovery & Enrichment
- **lyrics_analysis.py** - Lyrics fetching and theme analysis
- **lyrics_discovery.py** - LLM-powered lyrics-based song discovery
- **playlist_discovery.py** - Spotify playlist-based candidate discovery
- **enhanced_audio_features.py** - Advanced Spotify audio feature analysis

### Legacy Systems (Deprecated)
- **candidate_verification.py** - Legacy regex-based verification (replaced by NLP)
- **voter_preferences.py** - Voter preference modeling (removed from Scout)

### Spotify Integration
- **spotify_playlist_creator.py** - Spotify playlist creation utilities
- **setup_audio_features_db.py** - Audio features database management

## Architecture

These libraries implement a three-tier text processing system:

1. **Conceptual Analysis** - Semantic similarity and theme matching
2. **Matching** - Fuzzy matching for song discovery and verification  
3. **Exact Identification** - Preservation of exact Spotify metadata

## Import Usage

The virtual environment automatically includes this directory in PYTHONPATH,
so imports work naturally:

```python
from forecasting import MusicForecaster
from nlp_text_processor import MusicTextProcessor
from setup_db import get_db_connection
```

## Documentation

Technical documentation is included in this directory:
- **NLP_MIGRATION_SUMMARY.md** - NLP system architecture and migration details
- **PREDICTION_GUIDE.md** - Music prediction algorithms and scoring methods
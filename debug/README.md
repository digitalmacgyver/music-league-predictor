# Debug Directory

This directory contains debugging, testing, analysis, and one-off scripts used during development.

## Organization

### Debug Scripts (`debug_*.py`)
Scripts for troubleshooting specific issues:
- `debug_spotify*.py` - Spotify API debugging
- `debug_vote*.py` - Vote parsing debugging  
- `debug_page.py` - Page scraping debugging
- etc.

### Analysis Scripts (`analyze_*.py`, `*_analysis.py`)
One-time research and analysis scripts:
- `analyze_bt26_voters.py` - BT26 voter analysis
- `corrected_bt26_analysis.py` - Corrected voter analysis
- `recent_leagues_analysis.py` - Recent league patterns
- etc.

### Test Scripts (`test_*.py`)
Unit tests and validation scripts:
- `test_vote_parsing.py` - Vote parsing tests
- `test_mainstream_filter.py` - Mainstream filter tests
- etc.

### One-off Scripts
Temporary or single-purpose scripts:
- `add_spotify_creds.py` - One-time credential setup
- `predict_food_theme.py` - Specific theme prediction
- `run.py` - Generic runner
- etc.

## Guidelines

**All future debugging, testing, and analysis scripts should be created in this directory** to keep the root directory clean and focused on core user workflows.

See `script_categorization.txt` for the complete list of moved scripts and their purposes.
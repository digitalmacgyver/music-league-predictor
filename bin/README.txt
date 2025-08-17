# bin/ Directory

This directory contains the main executable scripts for the Music League project.

## Main Executables

### Core Applications
- **scout.py** - Intelligence song recommendation engine for Music League themes
- **scraper.py** - Web scraper for extracting Music League data via Spotify SSO
- **reports.py** - Generate analytical reports from the collected database

### Setup & Authentication
- **login.py** - Interactive Spotify authentication helper
- **setup_spotify.py** - Configure Spotify API credentials
- **setup_anthropic.py** - Configure Anthropic API credentials for LLM features

### Validation & Monitoring
- **validate_spotify.py** - Test Spotify API connectivity and credentials
- **validate_anthropic.py** - Test Anthropic API connectivity and credentials  
- **validate_full_system.py** - Comprehensive system validation
- **monitor.py** - System monitoring and health checks

### Authentication Utilities
- **spotify_auth_helper.py** - Spotify OAuth flow utilities
- **spotify_auth_server.py** - Local OAuth callback server

## Usage

All scripts require the virtual environment to be activated first:

```bash
# From project root - activate virtual environment first
source venv/bin/activate

# Then run scripts
./bin/scout.py "Songs about food" --verbose
./bin/scraper.py update
./bin/reports.py
```

The virtual environment automatically sets PYTHONPATH to include the lib/ directory,
so all library imports work correctly. Scripts use the standard `#!/usr/bin/env python3` 
hashbang and rely on the activated environment.

## Documentation

User guides and setup instructions are included in this directory:
- **SCOUT_GUIDE.md** - Comprehensive Scout usage documentation
- **SCRAPER.md** - Web scraper setup and usage guide
- **SPOTIFY_SETUP.md** - Spotify API configuration instructions
- **USAGE_GUIDE.md** - General project usage guide
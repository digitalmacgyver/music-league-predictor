# Music League Web Scraper

A comprehensive web scraper for Music League that handles Spotify SSO authentication and extracts historical league data into a SQLite database.

## Features

- **Spotify SSO Authentication**: Handles OAuth flow through Spotify login
- **Session Persistence**: Saves authentication state to avoid repeated logins
- **Dynamic Content Handling**: Scrolls pages to load all lazy-loaded content
- **Comprehensive Data Extraction**: Captures leagues, rounds, songs, and individual votes
- **Error Recovery**: Implements retry logic and graceful error handling
- **Progress Tracking**: Saves scraping progress to resume from interruptions
- **Flexible Filtering**: Can filter leagues by name or scrape all leagues
- **Detailed Reports**: Generates various reports from collected data

## Quick Start

1. Clone this repository
2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the package in editable mode (this sets up all dependencies and paths):
```bash
pip install -e .
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

**Important**: Always activate the virtual environment before running any scripts:
```bash
source venv/bin/activate
```

The virtual environment automatically configures Python paths for the lib/ modules.

## Configuration

Edit `config.py` to customize:

- `LEAGUE_FILTER`: Set to "Bard's Tale" to filter specific leagues (default)
- `SCRAPE_ALL_LEAGUES`: Set to `True` to scrape all leagues regardless of filter
- `HEADLESS_MODE`: Set to `True` to run browser in background (default: `False` for authentication)
- `REQUEST_DELAY_MIN/MAX`: Adjust rate limiting between requests

## Usage

### 1. Setup Database

First time only - create the database schema:

```bash
./bin/setup_db.py
```

This creates `data/music_league.db` with all necessary tables and views.

### 2. Run the Scout (Song Recommendation Engine)

```bash
./bin/scout.py "Songs about Food" -n 20 --verbose
```

### 3. Run the Web Scraper

```bash
./bin/scraper.py
```

### 4. Generate Reports

```bash
./bin/reports.py
```

### 5. Authentication & Scraping

**Authenticate (first time or when session expires):**
```bash
./bin/login.py
```
- Browser window opens to Music League login
- Complete Spotify SSO authentication manually
- Press Enter when on completed leagues page
- Session saved for future use

### 6. Project Structure

- **bin/**: Executable scripts (scout.py, scraper.py, reports.py, setup tools)
- **lib/**: Core library modules (forecasting, NLP, database utilities)  
- **debug/**: Debug and testing scripts
- **reports/**: Generated reports and analytics
- **data/**: Database files and scraped content

## Configuration

Set up your API credentials in `.env` file:
```bash
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Database Schema

The system uses these main tables:
- **leagues**: League information (id, title, url)
- **rounds**: Round details (id, league_id, number, title, description)  
- **songs**: Song submissions (id, round_id, title, artist, album, submitter, votes)
- **votes**: Individual votes (song_id, voter, points, comment)

## Error Handling

The scraper includes comprehensive error handling:

- **Authentication failures**: Prompts for manual re-authentication
- **Network errors**: Automatic retries with exponential backoff
- **Missing elements**: Logs warnings and continues with next item
- **Database errors**: Rolls back transactions and logs errors
- **Interruptions**: Progress tracking allows resuming from last successful point

## Performance Considerations

- **Rate Limiting**: Configurable delays between requests (1-3 seconds default)
- **Scroll Detection**: Automatically detects when all content is loaded
- **Batch Processing**: Saves data in batches to minimize database writes
- **Memory Management**: Processes one league/round at a time

## Troubleshooting

**Authentication Issues:**
- Ensure you're using correct Spotify credentials
- Check if your account has access to Music League
- Try deleting `data/session_state.json` to force re-authentication

**Missing Data:**
- The scraper uses flexible selectors that may need adjustment if the site structure changes
- Check `data/scraper.log` for warnings about missing elements
- Selectors can be updated in `config.py`

**Database Errors:**
- Run `python setup_db.py` to recreate the database schema
- Check file permissions on the `data/` directory

**Browser Issues:**
- Ensure Playwright browsers are installed: `playwright install chromium`
- Try running with `HEADLESS_MODE = False` to see what's happening

## Legal and Ethical Considerations

- This scraper respects rate limits to avoid overloading the server
- Only scrapes data you have access to as an authenticated user
- Stores data locally for personal use
- Always comply with Music League's Terms of Service

## License

This project is for educational purposes. Please respect Music League's terms of service and use responsibly.
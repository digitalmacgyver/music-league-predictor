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

## Installation

1. Clone or download this repository

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

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
python setup_db.py
```

This creates `data/music_league.db` with all necessary tables and views.

### 2. Authentication & Scraping

#### Option A: Automatic (Recommended)
```bash
./run.py
```
This handles authentication and scraping automatically.

#### Option B: Manual Steps

**Authenticate (first time or when session expires):**
```bash
./login.py
```
- Browser window opens to Music League login
- Complete Spotify SSO authentication manually
- Press Enter when on completed leagues page
- Session saved for future use

**Run scraper:**
```bash
./scraper.py
```
- Uses saved session cookies
- No authentication prompts
- Clear error messages if session expired

### 3. Generate Reports

After scraping, generate reports from the collected data:

```bash
python reports.py
```

Available reports:
1. **All Songs**: Complete list of submitted songs
2. **Distinct Songs**: Unique songs with submission counts
3. **Best Songs**: Top 5 songs by vote total
4. **Worst Songs**: Bottom 5 songs by vote total
5. **Database Statistics**: Overview of collected data

## Database Schema

The scraper creates the following tables:

- **leagues**: League information (id, title, url)
- **rounds**: Round details (id, league_id, number, title, description)
- **songs**: Song submissions (id, round_id, title, artist, album, submitter, votes)
- **votes**: Individual votes (song_id, voter, points, comment)
- **scraping_progress**: Tracks scraping status for resumability

## Project Structure

```
music_league/
├── scraper.py          # Main scraping logic
├── setup_db.py         # Database schema creation
├── config.py           # Configuration settings
├── reports.py          # Report generation
├── requirements.txt    # Python dependencies
├── data/              # Created on first run
│   ├── music_league.db    # SQLite database
│   ├── session_state.json # Saved authentication
│   └── scraper.log        # Execution logs
```

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
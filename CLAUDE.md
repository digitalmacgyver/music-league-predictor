# Music League Data Scraper & Preference Predictor

## Project Overview
This project creates an intelligent music selection system for competitive Music Leagues, where participants submit songs matching themes and vote on each other's submissions (0-5 points per song, 10 total votes per person). The system will learn from historical data to predict which songs will score highly based on voter preferences and comments.

### Key Objectives
1. **Data Collection**: Scrape and archive 27 prior "Bard's Tale" Music Leagues from musicleague.com
2. **Preference Analysis**: Use NLP on comments and voting patterns to understand individual voter preferences
3. **Song Selection**: Build a predictive model to select optimal Spotify songs for future themes

## Current Milestone: Data Collection
This directory holds a set of utility scripts in Python which combine
to gather data from the Music League website and store them in a
SQLite Database.

## Architecture Decisions

### Data Storage: SQLite
- Chosen for relational data integrity and query flexibility
- Enables complex analytical queries for pattern recognition
- Portable and requires no server setup
- Easy migration path to PostgreSQL if needed

### Scraping Strategy
- Uses Selenium/Playwright for dynamic content handling
- Implements scroll-based content loading for complete data capture
- Handles Spotify SSO authentication flow
- Respects rate limits and implements retry logic

## Technical Components

### 1. Authentication Module
- Handles Spotify SSO login flow at https://app.musicleague.com/login/
- Options: Interactive browser window, credential storage, or cookie reuse
- Maintains session for authenticated scraping

### 2. League Scraper
- Starts at https://app.musicleague.com/completed/
- Identifies all "Bard's Tale" leagues (27 total)
- Extracts league metadata and URLs

### 3. Data Extraction Pipeline
For each league:
- **League Level**: Title, ID, participants
- **Round Level**: Number, title, description, theme
- **Song Level**: Title, artist, album, submitter, submission comments
- **Vote Level**: Voter, points (0-5), comment

### 4. Database Schema

```sql
leagues (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  created_at TIMESTAMP
)

rounds (
  id TEXT PRIMARY KEY,
  league_id TEXT REFERENCES leagues(id),
  round_number INTEGER,
  title TEXT,
  description TEXT
)

songs (
  id TEXT PRIMARY KEY,
  round_id TEXT REFERENCES rounds(id),
  title TEXT,
  artist TEXT,
  album TEXT,
  spotify_id TEXT,
  submitter_user TEXT,
  submission_comment TEXT,
  total_votes INTEGER,
  num_voters INTEGER
)

votes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  song_id TEXT REFERENCES songs(id),
  voter_user TEXT,
  points INTEGER CHECK (points >= 0 AND points <= 5),
  comment TEXT
)

users (
  username TEXT PRIMARY KEY,
  display_name TEXT
)
```

### 5. Reporting Module
- All songs submitted across leagues
- Distinct songs with submission counts
- Top performing songs by vote total
- Bottom performing songs
- User preference profiles

## Future Milestones

### Milestone 2: Preference Analysis
- NLP processing of vote comments
- User preference clustering
- Theme-based performance patterns
- Temporal preference evolution

### Milestone 3: Predictive Model
- Feature engineering from historical data
- ML model for song score prediction
- Integration with Spotify API for candidate songs
- Recommendation engine with explanations

## Implementation Notes

### Dynamic Content Handling
- Music League uses lazy loading for league tiles
- Implement scroll-to-bottom detection
- Wait for XHR requests to complete
- Verify data completeness with expected counts

### Error Handling
- Retry failed requests with exponential backoff
- Log all scraping attempts for debugging
- Checkpoint progress to resume interrupted scrapes
- Validate data integrity post-scrape

### Performance Considerations
- Implement concurrent scraping where possible
- Cache authentication tokens
- Batch database insertions
- Monitor rate limits to avoid blocking

## Development Guidelines

### Code Organization
- **Core scripts**: Keep main user workflows in root directory (login, scraper, scout, reports)
- **Debug scripts**: All troubleshooting, testing, and ad-hoc analysis scripts go in `debug/` directory
- **Libraries**: Core functionality modules stay in root (forecasting.py, voter_preferences.py, etc.)

### Debug Directory Usage
When creating scripts for:
- Debugging specific issues (e.g., `debug_spotify.py`)
- One-time analysis tasks (e.g., `analyze_bt26_voters.py`)
- Testing specific functionality (e.g., `test_vote_parsing.py`)
- Temporary troubleshooting (e.g., `debug_spotipy_url.py`)

**ALWAYS create them in the `debug/` directory** to keep the root clean and organized.

## Success Metrics
- Complete data capture from all 27 Bard's Tale leagues
- Zero data loss or corruption
- Ability to generate all specified reports
- Foundation ready for ML pipeline
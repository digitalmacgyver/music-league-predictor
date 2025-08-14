# Scout: Music League Song Recommendation Engine

## Overview

Scout is an intelligent, end-to-end recommendation system that automatically discovers and ranks candidate songs for any Music League theme. It requires **no manual song input** - Scout finds candidates using multiple discovery strategies and ranks them using our forecasting system.

## Quick Start

```bash
# Basic usage - get 10 recommendations for any theme
./scout.py "Songs about travel"

# Get 15 summer songs from the 80s
./scout.py "Summer songs" --number 15 --era 80s

# Rock songs about love with minimum quality threshold
./scout.py "Love songs" --genre rock --min-score 0.4

# Detailed output with discovery process
./scout.py "Sad songs" --verbose

# Export results as JSON
./scout.py "Happy songs" --output json > happy_songs.json
```

## Core Features

### 🔍 **Automatic Song Discovery**
Scout discovers candidates using 6 intelligent strategies:

1. **Historical Analysis**: Finds songs that succeeded in similar past themes
2. **Keyword Matching**: Searches for songs with theme-relevant titles
3. **Genre Targeting**: Uses genre-specific song pools
4. **Era Focusing**: Draws from decade-specific artist catalogs
5. **Spotify Search**: Leverages Spotify's catalog for theme searches
6. **Pattern Recognition**: Uses common theme patterns (colors, emotions, etc.)

### 🎯 **Smart Scoring System**
- **LLM Theme Analysis**: Uses Claude to understand abstract themes
- **Audio Feature Matching**: Matches songs to theme characteristics
- **Historical Performance**: Weights based on past Music League success
- **Duplicate Filtering**: Automatically excludes previously submitted songs

### 📊 **Multiple Output Formats**
- **Text**: Human-readable recommendations with details
- **JSON**: Structured data for programmatic use
- **CSV**: Spreadsheet-compatible format

## Command Line Options

### Required
- `theme` - The Music League theme (e.g., "Songs about food")

### Optional Parameters
- `--number/-n` - Number of recommendations (default: 10)
- `--description/-d` - Additional theme details for better analysis
- `--min-score` - Minimum prediction score (0.0-1.0, default: 0.0)
- `--era` - Focus on specific decade (60s, 70s, 80s, 90s, 00s, 10s, 20s)
- `--genre` - Focus on genre (rock, pop, country, hip-hop, electronic, folk, jazz, classical)
- `--exclude-artists` - Comma-separated list of artists to avoid
- `--include-obscure` - Include less mainstream options
- `--exclude-mainstream` - Exclude extremely popular songs (1B+ streams, radio classics)
- `--verbose/-v` - Show detailed discovery process
- `--output/-o` - Output format (text, json, csv)

## Example Workflows

### 🎵 **Theme-Specific Recommendations**

```bash
# Food songs (our tested example)
./scout.py "Songs about food" --number 5

# Travel songs with era filter
./scout.py "Songs about travel" --era 70s --number 8

# Color songs with genre focus
./scout.py "Songs with colors in the title" --genre pop --min-score 0.3
```

### 🎯 **Strategic Discovery**

```bash
# High-quality recommendations only
./scout.py "Breakup songs" --min-score 0.5 --number 5

# Avoid overused artists
./scout.py "Love songs" --exclude-artists "Taylor Swift,Ed Sheeran" --number 10

# Exclude extremely popular songs (avoid obvious picks)
./scout.py "Summer songs" --exclude-mainstream --number 8

# Include deeper cuts
./scout.py "Songs about rain" --include-obscure --era 90s

# Strategic combination: avoid mainstream but include quality obscure songs
./scout.py "Happy songs" --exclude-mainstream --include-obscure --min-score 0.4
```

### 📈 **Analysis and Export**

```bash
# Detailed discovery process
./scout.py "Christmas songs" --verbose --number 15

# Export for further analysis
./scout.py "Summer songs" --output json --number 20 > summer_analysis.json

# CSV for spreadsheet use
./scout.py "Sad songs" --output csv --era 80s > sad_80s.csv
```

## Understanding the Output

### Text Format
```
1. Song Title by Artist Name
   Combined Score: 0.750
   Theme Match: 0.800 | Audio Features: 0.650
   Details: Discovery method, scoring breakdown, audio characteristics
```

### Score Interpretation
- **Combined Score**: Overall recommendation strength (0.0-1.0)
  - 0.8+ = Excellent pick, very likely to succeed
  - 0.6-0.8 = Strong candidate
  - 0.4-0.6 = Decent option
  - <0.4 = Risky choice

- **Theme Match**: How well the song fits the theme (0.0-1.0)
- **Audio Features**: Musical characteristics alignment (0.0-1.0)

## Mainstream Filtering Details

### What Gets Filtered with `--exclude-mainstream`

**Streaming Giants (1B+ streams):**
- Shape of You, Blinding Lights, Bad Guy, Watermelon Sugar, etc.
- Songs that appear on every "most streamed" list

**All-Time Classics:**
- Bohemian Rhapsody, Stairway to Heaven, Hotel California, etc.
- Songs that appear on every "greatest of all time" list

**Radio Staples:**
- Don't Stop Believin', Sweet Caroline, Mr. Brightside, etc.
- Songs played constantly on classic rock/pop radio

**Wedding/Party Standards:**
- Dancing Queen, I Wanna Dance with Somebody, September, etc.
- Songs everyone expects at celebrations

**Mainstream Artist Mega-Hits:**
- Biggest hits from Taylor Swift, Ed Sheeran, Adele, Drake, etc.
- Songs that dominated charts and cultural zeitgeist

### Strategy Benefits
- **Avoid duplicates**: Multiple people likely to pick obvious songs
- **Stand out**: Less predictable choices get noticed
- **Discover gems**: Force exploration of deeper catalogs
- **Strategic advantage**: While others compete over popular songs, you find unique picks

### When to Use
✅ **Use `--exclude-mainstream` when:**
- Theme has obvious popular song choices
- Want to stand out from the crowd
- Looking for strategic advantage
- Competing with music enthusiasts who know the obvious picks

❌ **Don't use when:**
- Theme is very specific/niche (few mainstream options anyway)
- Playing with casual music fans (popular songs might actually win)
- Want maximum broad appeal regardless of uniqueness

## Discovery Strategy Details

### Historical Analysis
- Searches past rounds with similar themes
- Prioritizes songs that scored >8 points historically
- Weights by original performance success

### Keyword Matching
- Extracts key terms from theme description
- Searches song titles in database
- Filters by historical average performance

### Genre/Era Targeting
- Uses curated artist pools for each decade
- Applies genre-specific characteristic patterns
- Balances mainstream appeal with thematic fit

### Spotify Integration
- Searches Spotify catalog for theme-related songs
- Provides access to broader song universe
- Handles search term variations automatically

## Tips for Best Results

### 🎯 **Theme Writing**
- **Be specific**: "Songs about unrequited love" > "Love songs"
- **Add context**: Use `--description` for complex themes
- **Consider scope**: Broader themes = more candidates

### ⚙️ **Parameter Tuning**
- **Use era filters** for nostalgic themes
- **Set min-score** to ensure quality (try 0.4-0.6)
- **Genre targeting** helps focus results
- **Exclude mainstream** to avoid obvious picks everyone will choose
- **Include obscure** for deep cuts and surprises
- **Verbose mode** shows discovery reasoning

### 📊 **Strategic Usage**
- **Start broad** then narrow with filters
- **Compare multiple runs** with different parameters
- **Check excluded songs** - often reveals good alternatives
- **Combine with manual curation** for final selection

## Integration with Existing Tools

Scout works seamlessly with the full Music League toolkit:

```bash
# Update database first
./scraper.py update

# Get recommendations
./scout.py "Your theme" --number 10 --verbose

# Test specific songs
./predict_food_theme.py  # (adapt for your theme)

# Generate reports
./reports.py
```

## Troubleshooting

### Common Issues

**"No candidates discovered"**
- Try broader theme description
- Remove restrictive filters (era, genre)
- Check theme spelling

**"No recommendations above minimum score"**
- Lower `--min-score` threshold
- Increase `--number` to see more options
- Add `--include-obscure` for more variety

**Low-quality recommendations**
- Add theme `--description` for context
- Use `--era` or `--genre` filters
- Increase `--min-score` threshold

### Performance Notes
- First run may be slower (LLM analysis)
- Spotify search adds discovery time but improves results
- `--verbose` shows where time is spent

## API Dependencies

- **Anthropic API**: Enhanced theme analysis (optional but recommended)
- **Spotify API**: Broader song discovery (optional, has fallback)
- **Local Database**: Historical analysis (required - run scraper first)

Scout gracefully degrades when APIs are unavailable, using fallback systems to maintain functionality.

---

**Scout transforms Music League strategy from guesswork to data-driven recommendations!** 🎵🎯
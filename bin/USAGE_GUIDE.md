# Music League Scout - Enhanced Usage Guide

## Overview
Scout is now enhanced with historical pattern analysis that adapts recommendations based on how your Music League group's preferences have evolved over time.

## Basic Usage

### Simple Recommendations
```bash
./scout.py "Songs about travel" --number 10
```

### With Historical Pattern Analysis
```bash
./scout.py "Ominous rock" --historical-patterns --verbose
```

### With Voter Personalization + Historical Patterns
```bash
./scout.py "Love songs" --voter "Joe Hayward" --historical-patterns --number 5
```

### Basic Usage (Ensemble Models Enabled by Default)
```bash
./scout.py "Epic rock anthems" --verbose
```

### Legacy Scoring (Disable Ensemble Models)
```bash
./scout.py "Songs about time" --legacy --verbose
```

### Basic Usage (Lyrics Discovery Enabled by Default)
```bash
./scout.py "Songs about heartbreak" --verbose
```

### Disable Lyrics Discovery
```bash
./scout.py "Simple search" --no-lyrics-discovery
```

### All Features Combined
```bash
./scout.py "Songs about time" --voter "Drew" --historical-patterns --number 5
```

## New Features

### Advanced Ensemble Models (Enabled by Default)

**What it does:**
- **Default behavior** - combines multiple scoring approaches using sophisticated machine learning
- Uses weighted ensembles, stacked models, and voting systems
- **Includes lyrical content analysis** - analyzes song lyrics for theme relevance using LLM
- Provides enhanced accuracy and confidence scoring
- Adapts predictions based on component reliability
- Use `--legacy` flag to disable and use simple scoring instead

**How it works:**
- **Weighted Ensemble**: Learns optimal weights for theme, audio, lyrical, voter, and historical scores
- **Stacked Models**: Meta-learners that combine predictions intelligently  
- **Lyrical Analysis**: Fetches song lyrics and analyzes theme relevance using LLM
- **Dynamic Weighting**: Adjusts weights based on component confidence levels
- **Voting Systems**: Multiple ensemble methods vote on final rankings

**Example Output:**
```
🤖 Initializing ensemble prediction models...
   ✅ Ensemble models initialized
   🎯 Will attempt ensemble training with historical data

🤖 Scoring 24 candidates with ensemble models...
   🎯 Top pick: 2112 by Rush (score: 0.847)

Ensemble: StackedEnsemble_rf, Score: 0.847 (conf: 0.95), Theme: 1.00, Audio: 0.75, Lyrics: 0.92
```

### Lyrical Content Analysis (Automatic)

**What it does:**
- **Automatically fetches song lyrics** from multiple sources (Genius API, fallback scraping)
- **LLM-powered analysis** - uses Claude to analyze how well lyrics match the theme
- **Intelligent caching** - stores lyrics to avoid repeated API calls
- **Graceful degradation** - continues without lyrics if unavailable

**How it works:**
- **Multi-source fetching**: Tries Genius API first, then fallback methods
- **LLM theme matching**: Analyzes lyrical content for theme relevance
- **Confidence weighting**: Adjusts lyrical score based on analysis confidence
- **Integrated scoring**: Adds lyrics as 25-30% of final prediction score

**Example Output:**
```
🎵 Analyzing lyrics for Hotel California by Eagles...
   ✅ Lyrics found via: genius_api  
   🎯 Lyrical theme relevance: 0.92 (confidence: 0.85)
   📝 Key themes: California, hotel setting, place-based narrative
```

### Lyrics-Based Discovery (Enabled by Default)

**What it does:**
- **Default behavior** - enhanced candidate discovery through lyrical content analysis
- **Multi-method search**: Historical lyrical patterns, reverse search, thematic associations
- **Hidden gems discovery** - finds thematically relevant songs missed by title-based search
- **LLM-powered suggestions** - generates thematically appropriate song candidates
- **Use `--no-lyrics-discovery` to disable** if you want faster, simpler discovery

**How it works:**
- **Historical Patterns**: Analyzes past successful songs to find similar lyrical themes
- **Reverse Search**: Searches cached lyrics for thematic keywords and content
- **Thematic Associations**: Uses LLM to suggest songs with relevant lyrical content
- **Integration**: Adds lyrics-discovered candidates to existing discovery methods

**Example Output:**
```
🎵 Searching for songs with thematically relevant lyrics...
   📝 Lyrics engine found 12 potential candidates
   🎯 Lyrical match: Trans-Europe Express by Kraftwerk (relevance: 0.70)
   🎯 Lyrical match: Ramblin' Man by The Allman Brothers Band (relevance: 0.90)
```

### Historical Pattern Analysis (`--historical-patterns`)

**What it does:**
- Analyzes your group's 26-league voting history
- Identifies if your current voter pool tends to be conservative or generous
- Adapts scoring to match group evolution patterns

**How it works:**
- **Conservative Groups**: Boosts songs with excellent theme matches (>0.8), penalizes weak matches (<0.5)
- **Generous Groups**: Boosts songs with interesting audio features
- **Confidence-based**: Only applies adjustments when prediction confidence is high (>70%)

**Example Output:**
```
📊 Initializing historical pattern analysis...
   ✅ Historical patterns loaded - Group tendency: generous
   📈 Confidence: 93.6%

🎯 Scoring 24 candidates...
   Scoring candidate 1/24
     Historical: 1.15 (generous group)
```

### Enhanced Scoring Weights

**Without historical patterns (with lyrics):**
- Theme Match: 40%
- Audio Features: 30%
- Lyrical Analysis: 30%

**With voter preferences + lyrics:**
- Theme Match: 30%
- Audio Features: 25%
- Lyrical Analysis: 25%
- Voter Preference: 20%

**With historical patterns + voter preferences + lyrics:**
- Theme Match: 25%
- Audio Features: 20%
- Lyrical Analysis: 25%
- Voter Preference: 20%
- Historical Adjustment: 10%

## Key Insights from Historical Analysis

### Group Evolution
- **40% average turnover** between leagues
- **Major conservatism shift**: Early leagues 1.70 avg → Recent leagues 1.30 avg (-0.40)
- **Increased consensus**: Rating disagreement dropped 50%

### Core Voters (70%+ participation)
1. **legion1996a**: 26 leagues, 1.45 avg (musical explorer)
2. **Joe Hayward**: 24 leagues, 1.20 avg (conservative critic)
3. **Drew**: 24 leagues, 1.50 avg (balanced)
4. **caliban**: 22 leagues, 1.55 avg (generous)

### Strategic Insights
- **Joe Hayward & Matt M**: Ultra-conservative quality control (1.20 avg)
- **High turnover periods**: Often trigger preference volatility
- **Recent trend**: More conservative, higher consensus

## Command Examples

### Conservative Group Strategy
```bash
./scout.py "Epic movie themes" --historical-patterns --exclude-mainstream
# Boosts high-quality theme matches, avoids risky selections
```

### Generous Group Strategy  
```bash
./scout.py "Songs with unusual instruments" --historical-patterns --include-obscure
# Boosts creative/interesting audio features
```

### Personal + Historical
```bash
./scout.py "Melancholy indie" --voter "Drew" --historical-patterns --era 10s
# Combines Drew's preferences with group tendency insights
```

### Conservative Voter Targeting
```bash
./scout.py "Songs about time" --voter "Joe Hayward" --historical-patterns
# Optimizes for conservative critics who value theme precision
```

## When to Use Historical Patterns

**Always recommended for:**
- Competitive leagues where precision matters
- Understanding group dynamics
- Long-term strategic planning

**Optional for:**
- Casual exploration
- Very quick searches
- When system is slow (adds 30-60 seconds)

## Output Interpretation

### Reasoning Codes
```
Discovery: llm_candidate_1, Theme: 0.80, Audio: 0.65, Historical: 1.15 (generous group)
```

- **Discovery**: How the song was found
- **Theme**: Theme matching score (0-1)
- **Audio**: Audio feature alignment (0-1)  
- **Historical**: Group tendency adjustment (0.7-1.2)
- **Group type**: conservative/generous/balanced

### Score Adjustments
- **1.2**: Major boost for excellent theme matches (conservative groups)
- **1.1**: Boost for interesting audio features (generous groups)
- **1.0**: No adjustment
- **0.7**: Penalty for weak theme matches (conservative groups)

## Performance Notes

- **Basic Scout**: ~10-20 seconds
- **+ Voter Preferences**: +5-10 seconds  
- **+ Historical Patterns**: +30-60 seconds (first run)
- **Subsequent runs**: Cached, ~10 seconds additional

The historical analysis provides strategic insights that can significantly improve song selection success rates by adapting to your group's evolved preferences.
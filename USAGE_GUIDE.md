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

## New Features

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

**Without historical patterns:**
- Theme Match: 60%
- Audio Features: 40%

**With voter preferences:**
- Theme Match: 40%
- Audio Features: 30%
- Voter Preference: 30%

**With historical patterns + voter preferences:**
- Theme Match: 35%
- Audio Features: 25%  
- Voter Preference: 25%
- Historical Adjustment: 15%

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
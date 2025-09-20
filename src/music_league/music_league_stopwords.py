"""
Music League specific stopwords and meta-terms to filter out from theme analysis

These terms commonly appear in theme descriptions but don't help identify 
relevant songs and often lead to spurious matches.
"""

import re

# Meta-terms about Music League itself that should be filtered
MUSIC_LEAGUE_META_TERMS = {
    # Common ML theme description terms
    'song', 'songs', 
    'track', 'tracks',
    'music', 'musical',
    'album', 'albums',
    'artist', 'artists', 'band', 'bands',
    'theme', 'themes', 'themed',
    'week', 'weeks', 'weekly',
    'submit', 'submission', 'submissions',
    'include', 'includes', 'including',
    'feature', 'features', 'featuring',
    'good', 'great', 'best', 'favorite',
    'cover', 'covers',  # When not talking about cover songs
    'version', 'versions',
    'record', 'records', 'recording',
    
    # Common instruction words in themes
    'must', 'should', 'need', 'needs',
    'pick', 'picks', 'choose', 'choice',
    'find', 'select', 'selection',
    'about', 'related', 'reference', 'references',
    'mention', 'mentions', 'contain', 'contains',
    'vote', 'votes', 'voting', 'point', 'points',
    
    # Generic time references that appear in many themes
    'time', 'times',
    'year', 'years', 
    'this', 'that', 'these', 'those',
    'next', 'last', 'first',
    'new', 'old',
    
    # Common filler words in descriptions
    'will', 'would', 'could', 'might',
    'want', 'wanted', 'like', 'liked',
    'make', 'makes', 'made',
    'just', 'really', 'actually', 
    'think', 'thought', 'feel', 'feeling',
    'know', 'known',
    
    # Words that describe the format
    'title', 'titles', 'name', 'names',
    'word', 'words', 'lyric', 'lyrics'
}

def should_filter_keyword(keyword: str) -> bool:
    """
    Check if a keyword should be filtered out as a Music League meta-term
    
    Args:
        keyword: The keyword to check
        
    Returns:
        True if the keyword should be filtered, False otherwise
    """
    return keyword.lower() in MUSIC_LEAGUE_META_TERMS


def filter_keywords(keywords: list) -> list:
    """
    Filter out Music League meta-terms from a list of keywords
    
    Args:
        keywords: List of keywords to filter
        
    Returns:
        Filtered list with meta-terms removed
    """
    return [kw for kw in keywords if not should_filter_keyword(kw)]


def extract_meaningful_theme_words(theme_text: str) -> list:
    """
    Extract only the meaningful words from a theme description,
    filtering out all the meta-terms about Music League itself
    
    Args:
        theme_text: The theme title and/or description
        
    Returns:
        List of meaningful keywords for song discovery
    """
    
    # Extract all words
    words = re.findall(r'\b[a-z]+\b', theme_text.lower())
    
    # Filter out meta-terms and very short words
    meaningful = [
        word for word in words 
        if len(word) > 2 and not should_filter_keyword(word)
    ]
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(meaningful))


def is_theme_about_music_format(theme_text: str) -> bool:
    """
    Check if a theme is specifically ABOUT music formats/albums/covers
    (as opposed to just using these words in the description)
    
    For example:
    - "Album Art" theme IS about albums (keep 'album' keyword)
    - "Songs about food" is NOT about songs (filter 'songs')
    """
    theme_lower = theme_text.lower()
    
    # Patterns that indicate the theme is ABOUT music format
    format_patterns = [
        r'\balbum\s+(art|cover|artwork)',
        r'\bcover\s+(art|version|song)',
        r'\bremix(es|ed)?\b',
        r'\blive\s+(version|performance|recording)',
        r'\bacoustic\s+(version|cover)',
        r'\b(demo|single|ep)\b.*theme'
    ]
    
    for pattern in format_patterns:
        if re.search(pattern, theme_lower):
            return True
    
    return False


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_themes = [
        "Album Art - This weeks theme is about album art. Submit a _good_ song from an album with _Great_ cover art!",
        "Songs about food - Pick tracks that mention eating, cooking, or meals",
        "British Invasion - Songs by British artists from the 1960s",
        "Cover songs - Submit your favorite cover versions",
        "One word titles - Songs with single-word titles"
    ]
    
    for theme in test_themes:
        print(f"\nTheme: {theme[:50]}...")
        keywords = extract_meaningful_theme_words(theme)
        print(f"Extracted keywords: {keywords}")
        
        # Check if it's about music format
        if is_theme_about_music_format(theme):
            print("  → Theme IS about music format (keep format keywords)")
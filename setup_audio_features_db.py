#!/usr/bin/env ./venv/bin/python3
"""
Set up SQLite database with historical Spotify audio features data

Imports CSV dataset and creates optimized lookup table for audio features
"""

import sqlite3
import pandas as pd
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import ast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioFeaturesDatabase:
    """Manages SQLite database for historical audio features"""
    
    def __init__(self, db_path: str = "audio_features.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to audio features database: {self.db_path}")
        
    def normalize_text(self, text: str) -> str:
        """Normalize text for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and normalize spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common words that cause matching issues
        remove_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = text.split()
        words = [w for w in words if w not in remove_words]
        
        return ' '.join(words)
    
    def parse_artists(self, artists_str: str) -> str:
        """Parse artists string and return normalized primary artist"""
        try:
            # Handle different formats: "['Artist1', 'Artist2']" or "Artist1"
            if artists_str.startswith('['):
                # Parse as Python list
                artists_list = ast.literal_eval(artists_str)
                if artists_list:
                    return self.normalize_text(artists_list[0])
            else:
                # Single artist string
                return self.normalize_text(artists_str)
        except:
            # Fallback to direct normalization
            return self.normalize_text(artists_str)
        
        return ""
    
    def create_tables(self):
        """Create audio features table with optimized structure"""
        cursor = self.conn.cursor()
        
        # Drop existing table if it exists
        cursor.execute("DROP TABLE IF EXISTS historical_audio_features")
        
        # Create new table with all audio features
        cursor.execute("""
            CREATE TABLE historical_audio_features (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                title_normalized TEXT NOT NULL,
                artist_normalized TEXT NOT NULL,
                search_key TEXT NOT NULL,
                
                -- Core audio features (matching Spotify API)
                acousticness REAL,
                danceability REAL,
                energy REAL,
                instrumentalness REAL,
                liveness REAL,
                loudness REAL,
                speechiness REAL,
                tempo REAL,
                valence REAL,
                mode INTEGER,
                key INTEGER,
                
                -- Additional metadata
                duration_ms INTEGER,
                year INTEGER,
                popularity INTEGER,
                explicit INTEGER,
                
                -- Indexes for fast lookup
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for fast lookup
        cursor.execute("CREATE INDEX idx_search_key ON historical_audio_features(search_key)")
        cursor.execute("CREATE INDEX idx_title_artist ON historical_audio_features(title_normalized, artist_normalized)")
        cursor.execute("CREATE INDEX idx_year ON historical_audio_features(year)")
        
        self.conn.commit()
        logger.info("Created historical_audio_features table with indexes")
    
    def import_spotify_dataset(self, csv_path: str):
        """Import Spotify dataset CSV into database"""
        logger.info(f"Importing Spotify dataset from: {csv_path}")
        
        # Read CSV file
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} tracks from CSV")
        
        # Show sample of data structure
        logger.info("CSV columns: " + ", ".join(df.columns.tolist()))
        logger.info("Sample data:")
        logger.info(df.head(2).to_string())
        
        # Clean and normalize data
        processed = 0
        errors = 0
        
        cursor = self.conn.cursor()
        
        for idx, row in df.iterrows():
            try:
                # Extract and normalize title/artist
                title = str(row.get('name', '')).strip()
                artists_raw = str(row.get('artists', ''))
                artist = self.parse_artists(artists_raw)
                
                if not title or not artist:
                    errors += 1
                    continue
                
                # Create normalized versions
                title_norm = self.normalize_text(title)
                artist_norm = self.normalize_text(artist)
                search_key = f"{title_norm} {artist_norm}".strip()
                
                # Extract audio features
                audio_features = {
                    'acousticness': float(row.get('acousticness', 0.5)),
                    'danceability': float(row.get('danceability', 0.5)),
                    'energy': float(row.get('energy', 0.5)),
                    'instrumentalness': float(row.get('instrumentalness', 0.0)),
                    'liveness': float(row.get('liveness', 0.1)),
                    'loudness': float(row.get('loudness', -10.0)),
                    'speechiness': float(row.get('speechiness', 0.05)),
                    'tempo': float(row.get('tempo', 120.0)),
                    'valence': float(row.get('valence', 0.5)),
                    'mode': int(row.get('mode', 1)),
                    'key': int(row.get('key', 5))
                }
                
                # Additional metadata
                duration_ms = int(row.get('duration_ms', 180000))
                year = int(row.get('year', 2000))
                popularity = int(row.get('popularity', 0))
                explicit = int(row.get('explicit', 0))
                
                # Insert into database
                cursor.execute("""
                    INSERT OR REPLACE INTO historical_audio_features (
                        id, title, artist, title_normalized, artist_normalized, search_key,
                        acousticness, danceability, energy, instrumentalness, liveness,
                        loudness, speechiness, tempo, valence, mode, key,
                        duration_ms, year, popularity, explicit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('id', f"track_{idx}"),
                    title, artist, title_norm, artist_norm, search_key,
                    audio_features['acousticness'], audio_features['danceability'],
                    audio_features['energy'], audio_features['instrumentalness'],
                    audio_features['liveness'], audio_features['loudness'],
                    audio_features['speechiness'], audio_features['tempo'],
                    audio_features['valence'], audio_features['mode'],
                    audio_features['key'], duration_ms, year, popularity, explicit
                ))
                
                processed += 1
                
                if processed % 10000 == 0:
                    logger.info(f"Processed {processed} tracks...")
                    self.conn.commit()
                    
            except Exception as e:
                errors += 1
                if errors < 10:  # Log first few errors
                    logger.warning(f"Error processing row {idx}: {e}")
        
        self.conn.commit()
        logger.info(f"Import complete! Processed: {processed}, Errors: {errors}")
        
        # Show statistics
        cursor.execute("SELECT COUNT(*) FROM historical_audio_features")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(year), MAX(year) FROM historical_audio_features")
        year_range = cursor.fetchone()
        
        logger.info(f"Database contains {total_count} tracks from {year_range[0]} to {year_range[1]}")
    
    def lookup_audio_features(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """Look up audio features for a song"""
        if not self.conn:
            self.connect()
            
        # Normalize inputs
        title_norm = self.normalize_text(title)
        artist_norm = self.normalize_text(artist)
        search_key = f"{title_norm} {artist_norm}".strip()
        
        cursor = self.conn.cursor()
        
        # Try exact search key match first
        cursor.execute("""
            SELECT * FROM historical_audio_features 
            WHERE search_key = ? 
            LIMIT 1
        """, (search_key,))
        
        result = cursor.fetchone()
        
        if not result:
            # Try fuzzy matching on title and artist separately
            cursor.execute("""
                SELECT * FROM historical_audio_features 
                WHERE title_normalized LIKE ? OR artist_normalized LIKE ?
                ORDER BY 
                    CASE 
                        WHEN title_normalized = ? AND artist_normalized = ? THEN 1
                        WHEN title_normalized = ? THEN 2
                        WHEN artist_normalized = ? THEN 3
                        ELSE 4
                    END
                LIMIT 1
            """, (f"%{title_norm}%", f"%{artist_norm}%", title_norm, artist_norm, title_norm, artist_norm))
            
            result = cursor.fetchone()
        
        if result:
            return dict(result)
        
        return None
    
    def get_statistics(self):
        """Get database statistics"""
        if not self.conn:
            self.connect()
            
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM historical_audio_features")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(year), MAX(year) FROM historical_audio_features")
        year_range = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(DISTINCT artist_normalized) FROM historical_audio_features")
        unique_artists = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT year, COUNT(*) as count 
            FROM historical_audio_features 
            GROUP BY year 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_years = cursor.fetchall()
        
        logger.info(f"Database Statistics:")
        logger.info(f"  Total tracks: {total:,}")
        logger.info(f"  Year range: {year_range[0]} - {year_range[1]}")
        logger.info(f"  Unique artists: {unique_artists:,}")
        logger.info(f"  Top years by track count:")
        for year, count in top_years:
            logger.info(f"    {year}: {count:,} tracks")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Set up audio features database"""
    
    # Path to downloaded dataset
    csv_path = "/home/viblio/coding_projects/music_league/data/spotify-data/data.csv"
    db_path = "/home/viblio/coding_projects/music_league/audio_features.db"
    
    if not Path(csv_path).exists():
        logger.error(f"Dataset not found at: {csv_path}")
        logger.info("Please ensure the Spotify dataset is downloaded first")
        return
    
    # Set up database
    db = AudioFeaturesDatabase(db_path)
    db.connect()
    
    try:
        # Create tables
        db.create_tables()
        
        # Import dataset
        db.import_spotify_dataset(csv_path)
        
        # Show statistics
        db.get_statistics()
        
        # Test lookup
        logger.info("\nTesting lookup functionality:")
        test_cases = [
            ("Bohemian Rhapsody", "Queen"),
            ("Hotel California", "Eagles"),
            ("Imagine", "John Lennon")
        ]
        
        for title, artist in test_cases:
            result = db.lookup_audio_features(title, artist)
            if result:
                logger.info(f"✅ Found: {result['title']} by {result['artist']} (year: {result['year']})")
                logger.info(f"   Audio: energy={result['energy']:.2f}, danceability={result['danceability']:.2f}")
            else:
                logger.info(f"❌ Not found: {title} by {artist}")
        
        logger.info(f"\n🎉 Audio features database ready at: {db_path}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
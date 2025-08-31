#!/usr/bin/env ./venv/bin/python3
"""
Database setup and schema creation for Music League data
"""

import sqlite3
from pathlib import Path
import logging
from music_league.config import DATABASE_PATH

logger = logging.getLogger(__name__)

def create_database():
    """Create the SQLite database with the required schema"""
    
    # Ensure data directory exists
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Create leagues table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leagues (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create rounds table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id TEXT PRIMARY KEY,
                league_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
                UNIQUE(league_id, round_number)
            )
        """)
        
        # Create songs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id TEXT NOT NULL,
                league_id TEXT NOT NULL,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                album TEXT,
                spotify_url TEXT,
                submitter TEXT NOT NULL,
                submitter_comment TEXT,
                total_votes_awarded INTEGER DEFAULT 0,
                final_score INTEGER DEFAULT 0,
                num_voters INTEGER DEFAULT 0,
                song_order INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE,
                FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
                UNIQUE(round_id, title, artist)
            )
        """)
        
        # Create votes table (formerly comments)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INTEGER NOT NULL,
                round_id TEXT NOT NULL,
                league_id TEXT NOT NULL,
                voter TEXT NOT NULL,
                points INTEGER CHECK(points >= 0 AND points <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
                FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE,
                FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
                UNIQUE(song_id, voter)
            )
        """)
        
        # Create scraping_progress table to track what's been scraped
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraping_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,  -- 'league', 'round', etc.
                entity_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
                last_attempted TIMESTAMP,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entity_type, entity_id)
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rounds_league ON rounds(league_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_songs_round ON songs(round_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_songs_league ON songs(league_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_song ON votes(song_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_round ON votes(round_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_league ON votes(league_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_entity ON scraping_progress(entity_type, entity_id)")
        
        # Create views for common queries
        
        # View for songs with full context
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_songs_full AS
            SELECT 
                s.id,
                s.title AS song_title,
                s.artist,
                s.album,
                s.submitter,
                s.submitter_comment,
                s.total_votes_awarded,
                s.final_score,
                s.num_voters,
                r.title AS round_title,
                r.description AS round_description,
                r.round_number,
                l.title AS league_title
            FROM songs s
            JOIN rounds r ON s.round_id = r.id
            JOIN leagues l ON s.league_id = l.id
        """)
        
        # View for top songs
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_top_songs AS
            SELECT 
                song_title,
                artist,
                album,
                total_votes_awarded,
                final_score,
                round_title,
                league_title
            FROM v_songs_full
            ORDER BY final_score DESC
        """)
        
        # View for distinct songs with submission count
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_distinct_songs AS
            SELECT 
                title AS song_title,
                artist,
                COUNT(*) AS submission_count,
                SUM(final_score) AS total_final_score_all_submissions
            FROM songs
            GROUP BY title, artist
            ORDER BY submission_count DESC, total_final_score_all_submissions DESC
        """)
        
        conn.commit()
        logger.info(f"Database created successfully at {DATABASE_PATH}")
        print(f"Database created successfully at {DATABASE_PATH}")
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def reset_database():
    """Drop all tables and recreate the database"""
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        logger.info("Existing database deleted")
    create_database()

def get_db_connection():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create the database
    create_database()
    
    # Verify creation
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("\nCreated tables:")
    for table in tables:
        print(f"  - {table['name']}")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = cursor.fetchall()
    
    print("\nCreated views:")
    for view in views:
        print(f"  - {view['name']}")
    
    conn.close()
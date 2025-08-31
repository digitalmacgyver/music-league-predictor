#!/usr/bin/env python3
"""
Monitor scraping progress
"""

import sqlite3
import time
from pathlib import Path
from music_league.config import DATABASE_PATH

def get_stats():
    """Get current database statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM leagues")
        leagues = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rounds")
        rounds = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM songs")
        songs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM votes")
        votes = cursor.fetchone()[0]
        
        # Get latest league being processed
        cursor.execute("SELECT title FROM leagues ORDER BY rowid DESC LIMIT 1")
        latest = cursor.fetchone()
        latest_league = latest[0] if latest else "None"
        
        conn.close()
        
        return {
            'leagues': leagues,
            'rounds': rounds, 
            'songs': songs,
            'votes': votes,
            'latest': latest_league
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    print("Music League Scraping Monitor")
    print("Press Ctrl+C to stop monitoring")
    print("="*50)
    
    try:
        while True:
            stats = get_stats()
            
            if 'error' in stats:
                print(f"Error: {stats['error']}")
            else:
                print(f"\rLeagues: {stats['leagues']:2d} | Rounds: {stats['rounds']:3d} | Songs: {stats['songs']:4d} | Votes: {stats['votes']:5d} | Latest: {stats['latest'][:30]:<30}", end='', flush=True)
            
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    main()
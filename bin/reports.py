#!/usr/bin/env python3
"""
Generate reports from Music League database
"""

import sqlite3
import sys
import subprocess
import tabulate
from config import DATABASE_PATH


def get_db_connection():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def report_all_songs():
    """List all songs submitted"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            s.title AS song,
            s.artist,
            s.album,
            r.description AS round_description,
            l.title AS league_description
        FROM songs s
        JOIN rounds r ON s.round_id = r.id
        JOIN leagues l ON s.league_id = l.id
        ORDER BY l.title, r.round_number, s.song_order
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*80)
    print("ALL SONGS SUBMITTED")
    print("="*80)
    
    if results:
        headers = ["Song", "Artist", "Album", "Round", "League"]
        rows = [[r["song"], r["artist"], r["album"], r["round_description"][:50], r["league_description"][:30]] 
                for r in results]
        print(tabulate.tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"\nTotal songs: {len(results)}")
    else:
        print("No songs found in database")


def report_distinct_songs():
    """List unique songs with submission count"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            title AS song,
            artist,
            COUNT(*) AS submission_count
        FROM songs
        GROUP BY title, artist
        ORDER BY submission_count DESC, title
        LIMIT 50
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*80)
    print("DISTINCT SONGS (Top 50 by submission count)")
    print("="*80)
    
    if results:
        headers = ["Song", "Artist", "Times Submitted"]
        rows = [[r["song"], r["artist"], r["submission_count"]] for r in results]
        print(tabulate.tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("No songs found in database")


def report_best_songs():
    """List songs with highest total votes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        WITH song_vote_totals AS (
            SELECT 
                s.title AS song,
                s.artist,
                SUM(v.points) AS actual_total_votes,
                r.title AS round_title,
                l.title AS league_description
            FROM songs s
            JOIN rounds r ON s.round_id = r.id
            JOIN leagues l ON s.league_id = l.id
            LEFT JOIN votes v ON v.song_id = s.rowid
            GROUP BY s.rowid, s.title, s.artist, r.title, l.title
        ),
        ranked_songs AS (
            SELECT 
                *,
                DENSE_RANK() OVER (ORDER BY actual_total_votes DESC) AS vote_rank
            FROM song_vote_totals
            WHERE actual_total_votes > 0
        )
        SELECT * FROM ranked_songs 
        WHERE vote_rank <= 5
        ORDER BY actual_total_votes DESC, song
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*80)
    print("BEST SONGS (Highest vote totals)")
    print("="*80)
    
    if results:
        headers = ["Song", "Artist", "Total Votes", "Round", "League"]
        rows = [[r["song"], r["artist"], r["actual_total_votes"], 
                r["round_title"][:40], r["league_description"][:25]] 
                for r in results]
        print(tabulate.tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("No songs with votes found in database")


def report_worst_songs():
    """List songs with lowest total votes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        WITH song_vote_totals AS (
            SELECT 
                s.title AS song,
                s.artist,
                COALESCE(SUM(v.points), 0) AS actual_total_votes,
                r.title AS round_title,
                l.title AS league_description
            FROM songs s
            JOIN rounds r ON s.round_id = r.id
            JOIN leagues l ON s.league_id = l.id
            LEFT JOIN votes v ON v.song_id = s.rowid
            GROUP BY s.rowid, s.title, s.artist, r.title, l.title
        ),
        ranked_songs AS (
            SELECT 
                *,
                DENSE_RANK() OVER (ORDER BY actual_total_votes ASC) AS vote_rank
            FROM song_vote_totals
        )
        SELECT * FROM ranked_songs 
        WHERE vote_rank <= 5
        ORDER BY actual_total_votes ASC, song
        LIMIT 20
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*80)
    print("WORST SONGS (Lowest vote totals)")
    print("="*80)
    
    if results:
        headers = ["Song", "Artist", "Total Votes", "Round", "League"]
        rows = [[r["song"], r["artist"], r["actual_total_votes"], 
                r["round_title"][:40], r["league_description"][:25]] 
                for r in results]
        print(tabulate.tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("No songs found in database")


def report_database_stats():
    """Show database statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Count leagues
    cursor.execute("SELECT COUNT(*) as count FROM leagues")
    stats['leagues'] = cursor.fetchone()['count']
    
    # Count rounds
    cursor.execute("SELECT COUNT(*) as count FROM rounds")
    stats['rounds'] = cursor.fetchone()['count']
    
    # Count songs
    cursor.execute("SELECT COUNT(*) as count FROM songs")
    stats['songs'] = cursor.fetchone()['count']
    
    # Count votes
    cursor.execute("SELECT COUNT(*) as count FROM votes")
    stats['votes'] = cursor.fetchone()['count']
    
    # Count unique voters
    cursor.execute("SELECT COUNT(DISTINCT voter) as count FROM votes")
    stats['unique_voters'] = cursor.fetchone()['count']
    
    # Count unique submitters
    cursor.execute("SELECT COUNT(DISTINCT submitter) as count FROM songs")
    stats['unique_submitters'] = cursor.fetchone()['count']
    
    conn.close()
    
    print("\n" + "="*80)
    print("DATABASE STATISTICS")
    print("="*80)
    
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value:,}")


def main():
    """Run all reports"""
    
    if not DATABASE_PATH.exists():
        print(f"Database not found at {DATABASE_PATH}")
        print("Please run the scraper first: python scraper.py")
        return
    
    print("\n" + "="*80)
    print("MUSIC LEAGUE REPORTS")
    print("="*80)
    
    # Show database stats first
    report_database_stats()
    
    # Ask user which report to run
    while True:
        print("\n" + "-"*40)
        print("Available Reports:")
        print("1. All Songs")
        print("2. Distinct Songs")
        print("3. Best Songs (Highest Votes)")
        print("4. Worst Songs (Lowest Votes)")
        print("5. Database Statistics")
        print("6. Run All Reports")
        print("0. Exit")
        print("-"*40)
        
        choice = input("\nSelect report (0-6): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            report_all_songs()
        elif choice == '2':
            report_distinct_songs()
        elif choice == '3':
            report_best_songs()
        elif choice == '4':
            report_worst_songs()
        elif choice == '5':
            report_database_stats()
        elif choice == '6':
            report_all_songs()
            report_distinct_songs()
            report_best_songs()
            report_worst_songs()
            report_database_stats()
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    # Add tabulate to requirements if not already there
    try:
        import tabulate
    except ImportError:
        print("Installing tabulate...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
        import tabulate
    
    main()
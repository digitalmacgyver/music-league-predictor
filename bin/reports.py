#!/usr/bin/env python3
"""
Generate reports from Music League database with export capabilities
"""

import sqlite3
import sys
import subprocess
import json
import csv
import os
from datetime import datetime
from pathlib import Path
import tabulate
import pandas as pd
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


def get_advanced_analytics():
    """Generate advanced analytics insights"""
    conn = get_db_connection()
    
    # Most active participants
    active_participants = pd.read_sql_query("""
        SELECT 
            submitter as participant,
            COUNT(*) as songs_submitted,
            AVG(COALESCE(s.total_votes, 0)) as avg_votes_received
        FROM songs s
        GROUP BY submitter
        ORDER BY songs_submitted DESC
        LIMIT 10
    """, conn)
    
    # Genre diversity analysis
    genre_analysis = pd.read_sql_query("""
        SELECT 
            r.title as round_title,
            COUNT(DISTINCT s.artist) as unique_artists,
            COUNT(*) as total_songs,
            ROUND(COUNT(DISTINCT s.artist) * 100.0 / COUNT(*), 2) as artist_diversity_pct
        FROM songs s
        JOIN rounds r ON s.round_id = r.id
        GROUP BY r.id, r.title
        ORDER BY artist_diversity_pct DESC
    """, conn)
    
    # Voting patterns
    voting_patterns = pd.read_sql_query("""
        SELECT 
            voter,
            COUNT(*) as votes_cast,
            AVG(points) as avg_points_given,
            MAX(points) as max_points_given
        FROM votes
        WHERE points > 0
        GROUP BY voter
        ORDER BY votes_cast DESC
        LIMIT 10
    """, conn)
    
    # League participation trends
    league_trends = pd.read_sql_query("""
        SELECT 
            l.title as league,
            COUNT(DISTINCT r.id) as rounds,
            COUNT(DISTINCT s.submitter) as unique_participants,
            COUNT(*) as total_submissions
        FROM leagues l
        JOIN rounds r ON l.id = r.league_id
        JOIN songs s ON r.id = s.round_id
        GROUP BY l.id, l.title
        ORDER BY unique_participants DESC
    """, conn)
    
    conn.close()
    
    return {
        'active_participants': active_participants,
        'genre_analysis': genre_analysis,
        'voting_patterns': voting_patterns,
        'league_trends': league_trends
    }


def export_data(data, export_format, filename_base, output_dir="reports"):
    """Export data in specified format"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if export_format.lower() == 'csv':
        filename = output_path / f"{filename_base}_{timestamp}.csv"
        if isinstance(data, pd.DataFrame):
            data.to_csv(filename, index=False)
        else:
            # Convert dict of rows to CSV
            with open(filename, 'w', newline='') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        print(f"Exported to: {filename}")
        
    elif export_format.lower() == 'json':
        filename = output_path / f"{filename_base}_{timestamp}.json"
        if isinstance(data, pd.DataFrame):
            data.to_json(filename, orient='records', indent=2)
        else:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        print(f"Exported to: {filename}")
        
    elif export_format.lower() == 'html':
        filename = output_path / f"{filename_base}_{timestamp}.html"
        if isinstance(data, pd.DataFrame):
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Music League Report: {filename_base}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .timestamp {{ color: #666; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <h1>Music League Report: {filename_base.replace('_', ' ').title()}</h1>
                <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                {data.to_html(escape=False, index=False)}
            </body>
            </html>
            """
            with open(filename, 'w') as f:
                f.write(html_content)
        print(f"Exported to: {filename}")


def export_comprehensive_report():
    """Export a comprehensive report with all analytics"""
    print("\nGenerating comprehensive analytics report...")
    
    # Get all data
    analytics = get_advanced_analytics()
    
    # Export each analysis
    export_data(analytics['active_participants'], 'csv', 'active_participants')
    export_data(analytics['active_participants'], 'html', 'active_participants')
    
    export_data(analytics['genre_analysis'], 'csv', 'genre_diversity_analysis')
    export_data(analytics['genre_analysis'], 'html', 'genre_diversity_analysis')
    
    export_data(analytics['voting_patterns'], 'csv', 'voting_patterns')
    export_data(analytics['voting_patterns'], 'html', 'voting_patterns')
    
    export_data(analytics['league_trends'], 'csv', 'league_participation_trends')
    export_data(analytics['league_trends'], 'html', 'league_participation_trends')
    
    # Generate summary insights
    insights = {
        'report_generated': datetime.now().isoformat(),
        'database_path': str(DATABASE_PATH),
        'insights': {
            'most_active_participant': analytics['active_participants'].iloc[0].to_dict() if not analytics['active_participants'].empty else None,
            'most_diverse_round': analytics['genre_analysis'].iloc[0].to_dict() if not analytics['genre_analysis'].empty else None,
            'top_voter': analytics['voting_patterns'].iloc[0].to_dict() if not analytics['voting_patterns'].empty else None,
            'largest_league': analytics['league_trends'].iloc[0].to_dict() if not analytics['league_trends'].empty else None
        }
    }
    
    export_data(insights, 'json', 'analytics_summary')
    
    print(f"\nComprehensive report exported to ./reports/ directory")
    print("Files generated:")
    print("  - active_participants (CSV, HTML)")
    print("  - genre_diversity_analysis (CSV, HTML)")
    print("  - voting_patterns (CSV, HTML)")
    print("  - league_participation_trends (CSV, HTML)")
    print("  - analytics_summary (JSON)")


def show_advanced_analytics():
    """Display advanced analytics in console"""
    analytics = get_advanced_analytics()
    
    print("\n" + "="*80)
    print("ADVANCED ANALYTICS")
    print("="*80)
    
    print("\n📊 MOST ACTIVE PARTICIPANTS")
    print("-" * 50)
    if not analytics['active_participants'].empty:
        print(tabulate.tabulate(
            analytics['active_participants'].head().values,
            headers=['Participant', 'Songs Submitted', 'Avg Votes Received'],
            tablefmt="grid"
        ))
    
    print("\n🎵 GENRE DIVERSITY BY ROUND")
    print("-" * 50)
    if not analytics['genre_analysis'].empty:
        print(tabulate.tabulate(
            analytics['genre_analysis'].head().values,
            headers=['Round', 'Unique Artists', 'Total Songs', 'Diversity %'],
            tablefmt="grid"
        ))
    
    print("\n🗳️  TOP VOTERS")
    print("-" * 50)
    if not analytics['voting_patterns'].empty:
        print(tabulate.tabulate(
            analytics['voting_patterns'].head().values,
            headers=['Voter', 'Votes Cast', 'Avg Points', 'Max Points'],
            tablefmt="grid"
        ))
    
    print("\n🏆 LEAGUE PARTICIPATION")
    print("-" * 50)
    if not analytics['league_trends'].empty:
        print(tabulate.tabulate(
            analytics['league_trends'].head().values,
            headers=['League', 'Rounds', 'Participants', 'Submissions'],
            tablefmt="grid"
        ))


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
        print("\n" + "-"*60)
        print("📊 MUSIC LEAGUE REPORTS & ANALYTICS")
        print("-"*60)
        print("Basic Reports:")
        print("1. All Songs")
        print("2. Distinct Songs")
        print("3. Best Songs (Highest Votes)")
        print("4. Worst Songs (Lowest Votes)")
        print("5. Database Statistics")
        print("6. Run All Basic Reports")
        print()
        print("Advanced Analytics:")
        print("7. Show Advanced Analytics")
        print("8. Export Comprehensive Report (CSV, JSON, HTML)")
        print("9. Export All Songs (CSV)")
        print()
        print("0. Exit")
        print("-"*60)
        
        choice = input("\nSelect option (0-9): ").strip()
        
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
        elif choice == '7':
            show_advanced_analytics()
        elif choice == '8':
            export_comprehensive_report()
        elif choice == '9':
            # Export all songs to CSV
            conn = get_db_connection()
            all_songs_df = pd.read_sql_query("""
                SELECT 
                    s.title AS song,
                    s.artist,
                    s.album,
                    s.submitter,
                    s.total_votes,
                    s.number_of_voters,
                    r.title AS round_title,
                    r.description AS round_description,
                    l.title AS league_title
                FROM songs s
                JOIN rounds r ON s.round_id = r.id
                JOIN leagues l ON s.league_id = l.id
                ORDER BY l.title, r.round_number, s.song_order
            """, conn)
            conn.close()
            export_data(all_songs_df, 'csv', 'all_songs_export')
            print("✅ All songs exported to CSV format")
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
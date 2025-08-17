#!/usr/bin/env python3
"""
LLM Cache Management Utility

Provides tools to manage, analyze, and maintain the LLM response cache.
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

import argparse
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import json

from llm_cache import LLMCache

def print_histogram(data: dict, title: str, max_width: int = 40):
    """Print a text histogram"""
    if not data:
        print("  No data available")
        return
    
    max_count = max(data.values()) if data else 1
    if max_count == 0:
        max_count = 1  # Avoid division by zero
    
    for label, count in sorted(data.items()):
        bar_width = int((count / max_count) * max_width)
        bar = '█' * bar_width
        print(f"  {label}: {bar} {count}")

def format_size(bytes_val: float) -> str:
    """Format bytes as human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"

def show_statistics(cache: LLMCache):
    """Display comprehensive cache statistics"""
    stats = cache.get_statistics()
    
    print("\n" + "=" * 60)
    print("📊 LLM CACHE STATISTICS")
    print("=" * 60)
    
    # Overall statistics
    print("\n📈 Overall Performance:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Total hits: {stats['total_hits']}")
    print(f"  Total misses: {stats['total_misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.1f}%")
    print(f"  Cache size: {stats['cache_size_mb']:.2f} MB")
    
    if stats['reset_time']:
        reset_time = datetime.fromisoformat(stats['reset_time'])
        print(f"  Last reset: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Top accessed prompts
    print("\n🔥 Top 10 Most Accessed Prompts:")
    if stats['top_accessed']:
        for i, entry in enumerate(stats['top_accessed'], 1):
            print(f"  {i}. [{entry['access_count']} hits] {entry['prompt_preview']}")
    else:
        print("  No entries in cache")
    
    # Creation date histogram
    print("\n📅 Cache Entries by Creation Date:")
    creation_histogram = defaultdict(int)
    for entry in stats['all_entries']:
        if entry['created_at']:
            date = datetime.fromisoformat(entry['created_at']).date()
            creation_histogram[date.isoformat()] += 1
    
    if creation_histogram:
        # Show last 7 days
        today = datetime.now().date()
        for i in range(7):
            date = (today - timedelta(days=i)).isoformat()
            count = creation_histogram.get(date, 0)
            if count > 0 or i < 3:  # Always show last 3 days
                print_histogram({date: count}, "", max_width=30)
    else:
        print("  No entries to display")
    
    # Access date histogram
    print("\n🕐 Cache Entries by Last Access Date:")
    access_histogram = defaultdict(int)
    for entry in stats['all_entries']:
        if entry['last_accessed']:
            date = datetime.fromisoformat(entry['last_accessed']).date()
            access_histogram[date.isoformat()] += 1
    
    if access_histogram:
        # Show last 7 days
        today = datetime.now().date()
        for i in range(7):
            date = (today - timedelta(days=i)).isoformat()
            count = access_histogram.get(date, 0)
            if count > 0 or i < 3:  # Always show last 3 days
                print_histogram({date: count}, "", max_width=30)
    else:
        print("  No entries to display")
    
    # Model distribution
    print("\n🤖 Cache Entries by Model:")
    model_counts = Counter(entry.get('model', 'unknown') for entry in stats['all_entries'])
    for model, count in model_counts.most_common():
        print(f"  {model}: {count} entries")
    
    print("\n" + "=" * 60)

def reset_cache(cache: LLMCache):
    """Reset the entire cache"""
    print("\n⚠️  WARNING: This will delete all cached LLM responses!")
    confirm = input("Are you sure you want to reset the cache? (yes/no): ")
    
    if confirm.lower() == 'yes':
        count = cache.clear_all()
        print(f"✅ Cache reset complete. Removed {count} entries.")
    else:
        print("❌ Cache reset cancelled.")

def prune_by_access(cache: LLMCache, days: int):
    """Remove entries not accessed in N days"""
    print(f"\n🧹 Pruning entries not accessed in the last {days} days...")
    removed = cache.prune_by_access_date(days)
    print(f"✅ Removed {removed} stale entries.")

def prune_by_creation(cache: LLMCache, days: int):
    """Remove entries created more than N days ago"""
    print(f"\n🧹 Pruning entries created more than {days} days ago...")
    removed = cache.prune_by_creation_date(days)
    print(f"✅ Removed {removed} old entries.")

def export_cache(cache: LLMCache, output_file: str):
    """Export cache statistics to JSON"""
    stats = cache.get_statistics()
    
    # Convert datetime objects to strings for JSON serialization
    export_data = {
        'export_time': datetime.now().isoformat(),
        'statistics': stats
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print(f"✅ Cache statistics exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description='LLM Cache Management Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show cache statistics
  ./llm_cache_manager.py --stats
  
  # Reset entire cache
  ./llm_cache_manager.py --reset
  
  # Remove entries not accessed in 7 days
  ./llm_cache_manager.py --prune-access 7
  
  # Remove entries created more than 30 days ago
  ./llm_cache_manager.py --prune-created 30
  
  # Export statistics to JSON
  ./llm_cache_manager.py --export cache_stats.json
  
  # Combine operations
  ./llm_cache_manager.py --prune-access 7 --stats
        """
    )
    
    parser.add_argument('--stats', action='store_true',
                       help='Show cache statistics and performance metrics')
    parser.add_argument('--reset', action='store_true',
                       help='Reset entire cache (delete all entries)')
    parser.add_argument('--prune-access', type=int, metavar='DAYS',
                       help='Remove entries not accessed in the last N days')
    parser.add_argument('--prune-created', type=int, metavar='DAYS',
                       help='Remove entries created more than N days ago')
    parser.add_argument('--export', type=str, metavar='FILE',
                       help='Export cache statistics to JSON file')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any([args.stats, args.reset, args.prune_access, args.prune_created, args.export]):
        parser.print_help()
        return
    
    # Initialize cache
    cache = LLMCache(verbose=args.verbose)
    
    try:
        # Execute requested operations
        if args.reset:
            reset_cache(cache)
        
        if args.prune_access:
            prune_by_access(cache, args.prune_access)
        
        if args.prune_created:
            prune_by_creation(cache, args.prune_created)
        
        if args.export:
            export_cache(cache, args.export)
        
        if args.stats:
            show_statistics(cache)
        
    finally:
        cache.close()

if __name__ == "__main__":
    main()
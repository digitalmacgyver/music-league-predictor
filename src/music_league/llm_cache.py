#!/usr/bin/env python3
"""
LLM Response Cache using DiskCache

Provides caching for Anthropic API calls with metadata tracking
and cache management utilities.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import diskcache
from pathlib import Path
from music_league.config import BASE_DIR

logger = logging.getLogger(__name__)

class LLMCache:
    """Cache for LLM API responses with metadata tracking"""
    
    def __init__(self, cache_dir: Optional[str] = None, verbose: bool = False):
        """
        Initialize LLM cache
        
        Args:
            cache_dir: Directory for cache storage (default: data/llm_cache)
            verbose: Enable verbose logging
        """
        if cache_dir is None:
            cache_dir = Path(BASE_DIR) / "data" / "llm_cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # Initialize DiskCache
        self.cache = diskcache.Cache(str(self.cache_dir))
        
        # Initialize global statistics if not present
        if 'global_stats' not in self.cache:
            self.cache['global_stats'] = {
                'total_hits': 0,
                'total_misses': 0,
                'reset_time': datetime.now().isoformat()
            }
    
    def _generate_key(self, prompt: str, model: str = None) -> str:
        """Generate a unique cache key from prompt and model"""
        # Include model in hash to avoid cross-model cache pollution
        content = f"{model or 'default'}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _truncate_prompt(self, prompt: str, max_length: int = 50) -> str:
        """Truncate prompt for logging"""
        if len(prompt) <= max_length:
            return prompt
        return prompt[:max_length] + "..."
    
    def get(self, prompt: str, model: str = None) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a prompt
        
        Args:
            prompt: The LLM prompt
            model: Model identifier (optional)
            
        Returns:
            Cached response dict or None if not found
        """
        key = self._generate_key(prompt, model)
        
        # Check if exists in cache
        if key not in self.cache:
            # Update miss counter
            stats = self.cache['global_stats']
            stats['total_misses'] += 1
            self.cache['global_stats'] = stats
            
            if self.verbose:
                truncated = self._truncate_prompt(prompt)
                logger.info(f"💨 Cache MISS for prompt: '{truncated}'")
            
            return None
        
        # Get cached entry
        entry = self.cache[key]
        
        # Update metadata
        entry['last_accessed'] = datetime.now().isoformat()
        entry['access_count'] += 1
        self.cache[key] = entry
        
        # Update hit counter
        stats = self.cache['global_stats']
        stats['total_hits'] += 1
        self.cache['global_stats'] = stats
        
        if self.verbose:
            truncated = self._truncate_prompt(prompt)
            logger.info(f"🎯 Cache HIT for prompt: '{truncated}' (accessed {entry['access_count']} times)")
        
        return entry['response']
    
    def set(self, prompt: str, response: Dict[str, Any], model: str = None) -> None:
        """
        Store response in cache with metadata
        
        Args:
            prompt: The LLM prompt
            response: The API response to cache
            model: Model identifier (optional)
        """
        key = self._generate_key(prompt, model)
        now = datetime.now().isoformat()
        
        entry = {
            'prompt': prompt,
            'response': response,
            'model': model,
            'created_at': now,
            'last_accessed': now,
            'access_count': 0,
            'prompt_preview': self._truncate_prompt(prompt, 100)
        }
        
        self.cache[key] = entry
        
        if self.verbose:
            truncated = self._truncate_prompt(prompt)
            logger.info(f"💾 Cached response for prompt: '{truncated}'")
    
    def get_or_compute(self, prompt: str, compute_fn, model: str = None) -> Dict[str, Any]:
        """
        Get from cache or compute and cache
        
        Args:
            prompt: The LLM prompt
            compute_fn: Function to compute response if not cached
            model: Model identifier (optional)
            
        Returns:
            Cached or computed response
        """
        # Try to get from cache
        cached = self.get(prompt, model)
        if cached is not None:
            return cached
        
        # Compute response
        response = compute_fn()
        
        # Cache it
        self.set(prompt, response, model)
        
        return response
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = self.cache.get('global_stats', {
            'total_hits': 0,
            'total_misses': 0,
            'reset_time': None
        })
        
        # Count entries and gather metadata
        entries = []
        for key in self.cache.iterkeys():
            if key == 'global_stats':
                continue
            entry = self.cache[key]
            entries.append({
                'created_at': entry.get('created_at'),
                'last_accessed': entry.get('last_accessed'),
                'access_count': entry.get('access_count', 0),
                'prompt_preview': entry.get('prompt_preview', ''),
                'model': entry.get('model', 'unknown')
            })
        
        # Calculate hit rate
        total_requests = stats['total_hits'] + stats['total_misses']
        hit_rate = (stats['total_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Find top accessed entries
        top_entries = sorted(entries, key=lambda x: x['access_count'], reverse=True)[:10]
        
        return {
            'total_entries': len(entries),
            'total_hits': stats['total_hits'],
            'total_misses': stats['total_misses'],
            'hit_rate': hit_rate,
            'reset_time': stats.get('reset_time'),
            'cache_size_mb': self.cache.volume() / (1024 * 1024),
            'top_accessed': top_entries,
            'all_entries': entries
        }
    
    def clear_all(self) -> int:
        """Clear entire cache and reset statistics"""
        count = len(list(self.cache.iterkeys())) - 1  # -1 for global_stats
        self.cache.clear()
        
        # Reset global statistics
        self.cache['global_stats'] = {
            'total_hits': 0,
            'total_misses': 0,
            'reset_time': datetime.now().isoformat()
        }
        
        if self.verbose:
            logger.info(f"🗑️  Cleared {count} cache entries")
        
        return count
    
    def prune_by_access_date(self, days: int) -> int:
        """Remove entries not accessed in the last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        
        for key in list(self.cache.iterkeys()):
            if key == 'global_stats':
                continue
            
            entry = self.cache[key]
            last_accessed = datetime.fromisoformat(entry.get('last_accessed', ''))
            
            if last_accessed < cutoff:
                del self.cache[key]
                removed += 1
        
        if self.verbose:
            logger.info(f"🧹 Pruned {removed} entries not accessed in {days} days")
        
        return removed
    
    def prune_by_creation_date(self, days: int) -> int:
        """Remove entries created more than N days ago"""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        
        for key in list(self.cache.iterkeys()):
            if key == 'global_stats':
                continue
            
            entry = self.cache[key]
            created_at = datetime.fromisoformat(entry.get('created_at', ''))
            
            if created_at < cutoff:
                del self.cache[key]
                removed += 1
        
        if self.verbose:
            logger.info(f"🧹 Pruned {removed} entries created more than {days} days ago")
        
        return removed
    
    def close(self):
        """Close the cache properly"""
        self.cache.close()


# Global cache instance
_global_cache = None

def get_llm_cache(verbose: bool = False) -> LLMCache:
    """Get or create the global LLM cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = LLMCache(verbose=verbose)
    return _global_cache
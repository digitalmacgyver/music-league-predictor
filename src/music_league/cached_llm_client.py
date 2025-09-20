#!/usr/bin/env python3
"""
Cached LLM Client Wrapper

Wraps Anthropic API calls with caching functionality.
"""

import os
import sys
import logging
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add lib directory to path if not already there
lib_dir = Path(__file__).parent
if str(lib_dir) not in sys.path:
    sys.path.insert(0, str(lib_dir))

from anthropic import Anthropic, APIStatusError, APIError, RateLimitError
from music_league.llm_cache import get_llm_cache

logger = logging.getLogger(__name__)

class CachedAnthropicClient:
    """Wrapper for Anthropic client with caching"""
    
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        """
        Initialize cached Anthropic client
        
        Args:
            api_key: Anthropic API key (uses env var if not provided)
            verbose: Enable verbose cache logging
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        # Disable Anthropic's built-in retries - we'll handle them ourselves
        self.client = Anthropic(
            api_key=self.api_key,
            max_retries=0  # Disable SDK retries
        ) if self.api_key else None
        self.cache = get_llm_cache(verbose=verbose)
        self.verbose = verbose
        
        # Configuration for 529 handling
        self.max_retries_529 = 3  # Max retries for overload errors
        self.base_wait_529 = 30  # Base wait time in seconds for 529 errors
        self.max_wait_529 = 300  # Max wait time (5 minutes)
        self.consecutive_529_errors = 0  # Track consecutive overload errors
        self.last_529_time = None  # Track when we last saw a 529
    
    def create_message(self, 
                      messages: List[Dict[str, str]], 
                      model: str = "claude-3-haiku-20240307",
                      max_tokens: int = 1000,
                      temperature: float = 0.7,
                      use_cache: bool = True,
                      **kwargs) -> Dict[str, Any]:
        """
        Create a message with caching
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            max_tokens: Maximum tokens in response
            temperature: Temperature for sampling
            use_cache: Whether to use cache (default: True)
            **kwargs: Additional arguments for the API
            
        Returns:
            API response dict
        """
        if not self.client:
            raise ValueError("Anthropic API key not configured")
        
        # Create a cache key from the request parameters
        # We cache based on messages, model, and temperature (not max_tokens)
        cache_key_content = {
            'messages': messages,
            'model': model,
            'temperature': temperature
        }
        prompt = str(cache_key_content)
        
        if use_cache:
            # Try to get from cache
            cached_response = self.cache.get(prompt, model)
            if cached_response is not None:
                return cached_response
        
        # Make actual API call with retry logic for 529 errors
        if self.verbose:
            logger.info(f"🌐 Making Anthropic API call (model: {model})")
        
        retries = 0
        while retries <= self.max_retries_529:
            try:
                # Don't pass max_retries to messages.create - it's set at client level
                response = self.client.messages.create(
                    messages=messages,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                
                # Reset 529 tracking on success
                if self.consecutive_529_errors > 0:
                    if self.verbose:
                        logger.info("✅ API recovered from overload state")
                self.consecutive_529_errors = 0
                self.last_529_time = None
                break
                
            except APIStatusError as e:
                if e.status_code == 529:
                    self.consecutive_529_errors += 1
                    self.last_529_time = time.time()
                    
                    if retries >= self.max_retries_529:
                        # Give up after max retries
                        logger.error(f"🚨 Anthropic API is overloaded (529 error). Tried {self.max_retries_529} times.")
                        logger.error("💡 The service is experiencing high load. Please try again later.")
                        logger.error("💡 Consider running during off-peak hours or reducing request rate.")
                        raise SystemExit("Exiting due to persistent API overload. Please try again later.")
                    
                    # Calculate exponential backoff with jitter
                    wait_time = min(
                        self.base_wait_529 * (2 ** retries) + random.uniform(0, 10),
                        self.max_wait_529
                    )
                    
                    logger.warning(f"⚠️  API overloaded (529). Waiting {wait_time:.1f} seconds before retry {retries + 1}/{self.max_retries_529}")
                    
                    if self.consecutive_529_errors >= 3:
                        logger.warning("🔄 Multiple consecutive overload errors detected. Consider pausing execution.")
                    
                    time.sleep(wait_time)
                    retries += 1
                    
                elif e.status_code == 503:
                    # Service unavailable - also use backoff
                    wait_time = 10 * (retries + 1)
                    logger.warning(f"⚠️  Service unavailable (503). Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                    if retries > 3:
                        raise
                else:
                    # Other errors - don't retry
                    raise
            except Exception as e:
                # Non-API errors
                raise
        
        # Convert response to dict for caching
        response_dict = {
            'id': response.id,
            'type': response.type,
            'role': response.role,
            'content': [{'type': c.type, 'text': c.text} for c in response.content],
            'model': response.model,
            'stop_reason': response.stop_reason,
            'stop_sequence': response.stop_sequence,
            'usage': {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            }
        }
        
        # Cache the response
        if use_cache:
            self.cache.set(prompt, response_dict, model)
        
        return response_dict
    
    def create_message_simple(self, 
                            prompt: str, 
                            model: str = "claude-3-haiku-20240307",
                            max_tokens: int = 1000,
                            temperature: float = 0.7,
                            use_cache: bool = True,
                            **kwargs) -> str:
        """
        Simple interface for single-turn conversations
        
        Args:
            prompt: The user prompt
            model: Model to use
            max_tokens: Maximum tokens in response
            temperature: Temperature for sampling
            use_cache: Whether to use cache (default: True)
            **kwargs: Additional arguments for the API
            
        Returns:
            Response text string
        """
        messages = [{"role": "user", "content": prompt}]
        
        response = self.create_message(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            use_cache=use_cache,
            **kwargs
        )
        
        # Extract text from response
        if response.get('content'):
            return response['content'][0].get('text', '')
        return ''
    
    def clear_cache(self):
        """Clear the LLM cache"""
        return self.cache.clear_all()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return self.cache.get_statistics()


# Global cached client instance
_global_client = None

def get_cached_anthropic_client(verbose: bool = False) -> CachedAnthropicClient:
    """Get or create the global cached Anthropic client"""
    global _global_client
    if _global_client is None:
        _global_client = CachedAnthropicClient(verbose=verbose)
    return _global_client


# Drop-in replacement functions for existing code
def analyze_theme_with_llm_cached(theme: str, description: str = "", verbose: bool = False) -> Dict[str, Any]:
    """
    Cached version of theme analysis with LLM
    
    This is a drop-in replacement for existing theme analysis functions
    """
    client = get_cached_anthropic_client(verbose=verbose)
    
    prompt = f"""Analyze this Music League theme and provide insights for song selection:

Theme: {theme}
{"Description: " + description if description else ""}

Provide:
1. Key emotional tones and moods that would fit
2. Musical characteristics that align with the theme
3. Potential genres that work well
4. Creative interpretation angles
5. Songs to avoid (what doesn't fit)

Format as JSON with keys: emotional_tones, musical_characteristics, suggested_genres, creative_angles, avoid"""

    response_text = client.create_message_simple(
        prompt=prompt,
        model="claude-3-haiku-20240307",
        max_tokens=1500,
        temperature=0.7
    )
    
    # Parse JSON response
    import json
    try:
        # Extract JSON from response
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        else:
            json_str = response_text
        
        return json.loads(json_str)
    except:
        # Fallback if JSON parsing fails
        return {
            'emotional_tones': [],
            'musical_characteristics': [],
            'suggested_genres': [],
            'creative_angles': [],
            'avoid': [],
            'raw_response': response_text
        }
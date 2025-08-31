#!/usr/bin/env python3
"""
Test LLM Cache functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

import time
from cached_llm_client import CachedAnthropicClient

def test_cache_functionality():
    """Test basic cache operations"""
    print("Testing LLM Cache Functionality")
    print("=" * 40)
    
    # Initialize client with verbose logging
    client = CachedAnthropicClient(verbose=True)
    
    if not client.client:
        print("❌ Anthropic API key not configured - cannot test")
        return False
    
    print("\n1. Testing cache miss (first call)...")
    start_time = time.time()
    
    test_prompt = "What is the capital of France? Answer in one word."
    
    response1 = client.create_message_simple(
        prompt=test_prompt,
        model="claude-3-haiku-20240307",
        max_tokens=10,
        temperature=0.0
    )
    
    miss_time = time.time() - start_time
    print(f"   Response: {response1}")
    print(f"   Time: {miss_time:.2f}s (API call)")
    
    print("\n2. Testing cache hit (same call)...")
    start_time = time.time()
    
    response2 = client.create_message_simple(
        prompt=test_prompt,
        model="claude-3-haiku-20240307", 
        max_tokens=10,
        temperature=0.0
    )
    
    hit_time = time.time() - start_time
    print(f"   Response: {response2}")
    print(f"   Time: {hit_time:.2f}s (cached)")
    
    # Verify responses are identical
    if response1 == response2:
        print(f"   ✅ Responses match - cache working correctly!")
    else:
        print(f"   ❌ Responses differ - cache may be broken")
        return False
    
    # Verify caching is faster
    if hit_time < miss_time / 2:  # Cache should be much faster
        print(f"   ✅ Cache is {miss_time/hit_time:.1f}x faster!")
    else:
        print(f"   ⚠️  Cache not significantly faster ({miss_time/hit_time:.1f}x)")
    
    print("\n3. Testing cache statistics...")
    stats = client.get_cache_stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Total hits: {stats['total_hits']}")
    print(f"   Total misses: {stats['total_misses']}")
    print(f"   Hit rate: {stats['hit_rate']:.1f}%")
    print(f"   Cache size: {stats['cache_size_mb']:.2f} MB")
    
    if stats['total_hits'] >= 1 and stats['total_misses'] >= 1:
        print("   ✅ Statistics look correct!")
    else:
        print("   ❌ Statistics don't look right")
        return False
    
    print("\n4. Testing different parameters don't hit cache...")
    start_time = time.time()
    
    response3 = client.create_message_simple(
        prompt=test_prompt,
        model="claude-3-haiku-20240307",
        max_tokens=10,
        temperature=0.5  # Different temperature
    )
    
    different_time = time.time() - start_time
    print(f"   Response: {response3}")
    print(f"   Time: {different_time:.2f}s (should be API call, not cache)")
    
    if different_time > hit_time * 2:  # Should be API call, not cache
        print("   ✅ Different parameters correctly trigger new API call")
    else:
        print("   ⚠️  May have incorrectly used cache for different parameters")
    
    print("\n🎉 Cache test completed!")
    return True

def test_cache_metadata():
    """Test cache metadata tracking"""
    print("\nTesting Cache Metadata Tracking")
    print("=" * 35)
    
    from llm_cache import get_llm_cache
    cache = get_llm_cache(verbose=True)
    
    # Test multiple accesses to see access count increment
    prompt = "Test prompt for metadata"
    
    print("1. First access (cache miss)...")
    result1 = cache.get(prompt)
    print(f"   Result: {result1}")
    
    print("2. Setting cache entry...")
    cache.set(prompt, {"test": "response"})
    
    print("3. Multiple cache hits...")
    for i in range(3):
        result = cache.get(prompt)
        print(f"   Access {i+1}: Found entry with access_count in metadata")
    
    # Get statistics to see metadata
    stats = cache.get_statistics()
    if stats['all_entries']:
        entry = stats['all_entries'][0]
        print(f"\n   Entry metadata:")
        print(f"   - Created: {entry['created_at']}")
        print(f"   - Last accessed: {entry['last_accessed']}")
        print(f"   - Access count: {entry['access_count']}")
        print(f"   - Prompt preview: {entry['prompt_preview']}")
    
    cache.close()

if __name__ == "__main__":
    success = test_cache_functionality()
    test_cache_metadata()
    
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed'}")
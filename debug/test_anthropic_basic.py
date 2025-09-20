#!/usr/bin/env python3
"""Test basic Anthropic API connectivity"""

import os
import sys
import time
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, '/home/viblio/coding_projects/music_league')
os.chdir('/home/viblio/coding_projects/music_league')

load_dotenv()

# Test 1: Direct Anthropic SDK
print("=" * 60)
print("TEST 1: Direct Anthropic SDK call")
print("=" * 60)

try:
    from anthropic import Anthropic
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ No ANTHROPIC_API_KEY found in environment")
    else:
        print(f"✅ API key found: {api_key[:10]}...")
        
        client = Anthropic(api_key=api_key, max_retries=0)
        
        print("\nAttempting simple API call...")
        start = time.time()
        
        try:
            message = client.messages.create(
                model="claude-3-haiku-20240307",  # Cheapest, fastest model
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'hi'"}]
            )
            elapsed = time.time() - start
            print(f"✅ SUCCESS! Response: {message.content[0].text}")
            print(f"   Time: {elapsed:.2f}s")
            
        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ FAILED after {elapsed:.2f}s")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error: {e}")
            
            # Check if it's a 529
            if hasattr(e, 'status_code'):
                print(f"   Status code: {e.status_code}")
            if hasattr(e, 'response'):
                print(f"   Response headers: {dict(e.response.headers)}")
                
except ImportError as e:
    print(f"❌ Cannot import Anthropic: {e}")

# Test 2: Our cached client
print("\n" + "=" * 60)
print("TEST 2: CachedAnthropicClient")
print("=" * 60)

try:
    from src.music_league.cached_llm_client import CachedAnthropicClient
    
    client = CachedAnthropicClient(verbose=True)
    
    print("\nAttempting cached client call...")
    start = time.time()
    
    try:
        response = client.create_message_simple(
            prompt="Say 'hello'",
            model="claude-3-haiku-20240307",
            max_tokens=10
        )
        elapsed = time.time() - start
        print(f"✅ SUCCESS! Response: {response}")
        print(f"   Time: {elapsed:.2f}s")
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ FAILED after {elapsed:.2f}s")
        print(f"   Error: {e}")
        
except ImportError as e:
    print(f"❌ Cannot import CachedAnthropicClient: {e}")

# Test 3: Check rate limit headers if available
print("\n" + "=" * 60)
print("TEST 3: Rate limit information")
print("=" * 60)

try:
    import requests
    
    # Try to get rate limit info
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        # Make a minimal request to check headers
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        
        print("Checking API endpoint directly...")
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "test"}]
            },
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
        
        # Check rate limit headers
        for header in ['x-ratelimit-limit', 'x-ratelimit-remaining', 'x-ratelimit-reset', 'retry-after']:
            if header in response.headers:
                print(f"  {header}: {response.headers[header]}")
                
        if response.status_code == 529:
            print("\n⚠️  API is currently overloaded (529)")
            if 'retry-after' in response.headers:
                print(f"  Retry after: {response.headers['retry-after']} seconds")
            print("\n  This is likely a temporary issue on Anthropic's side.")
            print("  The API is experiencing high load.")
            
except Exception as e:
    print(f"❌ Direct API check failed: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

# Check if we're in a 529 storm
import glob
import datetime

log_files = glob.glob('/home/viblio/coding_projects/music_league/*.log')
if log_files:
    print("\nChecking recent log files for 529 patterns...")
    for log_file in log_files[:1]:  # Just check the most recent
        with open(log_file, 'r') as f:
            lines = f.readlines()[-100:]  # Last 100 lines
            five29_count = sum(1 for line in lines if '529' in line)
            if five29_count > 0:
                print(f"  Found {five29_count} occurrences of '529' in recent logs")
                
print("\nRecommendations:")
print("1. If getting constant 529s, wait 5-10 minutes for API to recover")
print("2. Consider using a different model (claude-3-haiku-20240307 is fastest)")
print("3. Check if API key has rate limits or billing issues")
print("4. Monitor https://status.anthropic.com for API status")
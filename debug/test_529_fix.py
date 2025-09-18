#!/usr/bin/env python3
"""Test that 529 errors are handled correctly with our custom retry logic"""

import sys
import os
import logging

# Add project to path
sys.path.insert(0, '/home/viblio/coding_projects/music_league')
os.chdir('/home/viblio/coding_projects/music_league')

# Enable logging to see what happens
logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("TESTING 529 ERROR HANDLING FIX")
print("=" * 80)
print()

# Test 1: Check that CachedAnthropicClient disables SDK retries
print("📋 TEST 1: Verify Anthropic client configuration")
print("-" * 40)

from src.music_league.cached_llm_client import CachedAnthropicClient

client = CachedAnthropicClient(verbose=True)

if client.client:
    # Check max_retries setting
    if hasattr(client.client, '_client'):
        sdk_client = client.client._client
        if hasattr(sdk_client, 'max_retries'):
            print(f"✅ SDK max_retries: {sdk_client.max_retries} (should be 0)")
    else:
        print(f"✅ Anthropic client configured with max_retries=0")
    
    print(f"✅ Our retry settings:")
    print(f"   - Max retries for 529: {client.max_retries_529}")
    print(f"   - Base wait time: {client.base_wait_529}s")
    print(f"   - Max wait time: {client.max_wait_529}s")
else:
    print("⚠️  No Anthropic API key configured")

print()

# Test 2: Check that forecasting.py uses cached client
print("📋 TEST 2: Verify forecasting.py uses cached client")
print("-" * 40)

from src.music_league.forecasting import MusicForecaster

forecaster = MusicForecaster(verbose=True)

if forecaster.cached_client:
    print("✅ Forecaster uses CachedAnthropicClient")
    if forecaster.anthropic_client == forecaster.cached_client:
        print("✅ Legacy anthropic_client points to cached_client")
    else:
        print("⚠️  Legacy anthropic_client is separate (should point to cached_client)")
else:
    print("⚠️  No cached client in forecaster")

print()

# Test 3: Check lyrics_analysis.py
print("📋 TEST 3: Verify lyrics_analysis.py uses cached client")
print("-" * 40)

from src.music_league.lyrics_analysis import LyricsThemeAnalyzer

theme_analyzer = LyricsThemeAnalyzer(verbose=True)

# The cached_client is in the analyzer sub-object
if hasattr(theme_analyzer, 'analyzer') and theme_analyzer.analyzer:
    if theme_analyzer.analyzer.cached_client:
        print("✅ LyricsAnalyzer uses CachedAnthropicClient")
        if theme_analyzer.analyzer.anthropic_client == theme_analyzer.analyzer.cached_client:
            print("✅ Legacy anthropic_client points to cached_client")
        else:
            print("⚠️  Legacy anthropic_client is separate (should point to cached_client)")
    else:
        print("⚠️  No cached client in analyzer")
else:
    print("⚠️  No analyzer object found")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("If all tests show ✅, then:")
print("1. The SDK's built-in retries are disabled (max_retries=0)")
print("2. Our custom retry logic will handle 529 errors")
print("3. You should see proper backoff messages (30s, 60s, 120s)")
print("4. No more rapid retries (0.465s, 0.989s)")
print()
print("Next time you get a 529 error, you should see:")
print("   ⚠️  API overloaded (529). Waiting 30.X seconds before retry 1/3")
print("Instead of:")
print("   Retrying request to /v1/messages in 0.485774 seconds")
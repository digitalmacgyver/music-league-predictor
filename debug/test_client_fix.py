#!/usr/bin/env python3
"""Test that the max_retries error is fixed"""

import sys
import os

# Add project to path
sys.path.insert(0, '/home/viblio/coding_projects/music_league')
os.chdir('/home/viblio/coding_projects/music_league')

from dotenv import load_dotenv
load_dotenv()

print("Testing CachedAnthropicClient...")

from src.music_league.cached_llm_client import CachedAnthropicClient

client = CachedAnthropicClient(verbose=True)

try:
    # This should work without 'max_retries' error
    response = client.create_message_simple('Say "Hello World"', max_tokens=10)
    print(f"✅ Success! Response: {response}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
print("\nTesting forecasting module...")

from src.music_league.forecasting import MusicForecaster

forecaster = MusicForecaster(verbose=False)

# Check that anthropic_client is None (not set to cached_client)
if forecaster.anthropic_client is None:
    print("✅ forecaster.anthropic_client is None (correct)")
else:
    print(f"❌ forecaster.anthropic_client is {type(forecaster.anthropic_client)} (should be None)")
    
if forecaster.cached_client:
    print("✅ forecaster.cached_client is set")
    
    # Test a simple call
    try:
        response = forecaster.cached_client.create_message_simple('Say "test"', max_tokens=10)
        print(f"✅ Cached client works: {response[:20]}...")
    except Exception as e:
        print(f"❌ Cached client error: {e}")
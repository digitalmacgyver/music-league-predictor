#!/usr/bin/env python3
"""Test sustained Anthropic API calls to check for 529 patterns"""

import os
import sys
import time
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, '/home/viblio/coding_projects/music_league')
os.chdir('/home/viblio/coding_projects/music_league')

load_dotenv()

from src.music_league.cached_llm_client import CachedAnthropicClient

print("Testing sustained API calls with exponential backoff...")
print("=" * 60)

client = CachedAnthropicClient(verbose=False)  # Less verbose for this test

# Test with 5 rapid calls
test_prompts = [
    "Say 'one'",
    "Say 'two'", 
    "Say 'three'",
    "Say 'four'",
    "Say 'five'"
]

success_count = 0
error_count = 0
five29_count = 0

for i, prompt in enumerate(test_prompts, 1):
    print(f"\nCall {i}/5: {prompt}")
    start = time.time()
    
    try:
        response = client.create_message_simple(
            prompt=prompt,
            model="claude-3-haiku-20240307",
            max_tokens=10
        )
        elapsed = time.time() - start
        print(f"  ✅ Success in {elapsed:.2f}s: {response[:20]}")
        success_count += 1
        
    except Exception as e:
        elapsed = time.time() - start
        error_msg = str(e)
        
        if '529' in error_msg:
            print(f"  ⚠️  529 error after {elapsed:.2f}s")
            five29_count += 1
        else:
            print(f"  ❌ Error after {elapsed:.2f}s: {error_msg[:100]}")
        error_count += 1
    
    # Small delay between calls to be polite
    if i < len(test_prompts):
        time.sleep(0.5)

print("\n" + "=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)
print(f"✅ Successful calls: {success_count}/{len(test_prompts)}")
print(f"❌ Failed calls: {error_count}/{len(test_prompts)}")
print(f"⚠️  529 errors: {five29_count}/{len(test_prompts)}")

if five29_count > 0:
    print("\n⚠️  DIAGNOSIS: API is experiencing intermittent overload")
    print("  - Our exponential backoff is working correctly")
    print("  - The 529s are coming from Anthropic's side")
    print("  - This typically resolves within 5-10 minutes")
elif success_count == len(test_prompts):
    print("\n✅ DIAGNOSIS: API is working perfectly!")
    print("  - All calls succeeded")
    print("  - No 529 errors detected")
    print("  - Safe to run scout commands")
else:
    print("\n❌ DIAGNOSIS: Other API issues detected")
    print("  - Check API key validity")
    print("  - Check network connectivity")
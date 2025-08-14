#!/usr/bin/env ./venv/bin/python3
"""
Test the mainstream filtering functionality
"""

from scout import SongScout

def test_mainstream_detection():
    """Test the mainstream song detection"""
    scout = SongScout(verbose=True)
    
    # Test cases - songs that should be filtered
    mainstream_test_cases = [
        ("Shape of You", "Ed Sheeran"),
        ("Bohemian Rhapsody", "Queen"), 
        ("Blinding Lights", "The Weeknd"),
        ("Bad Guy", "Billie Eilish"),
        ("Watermelon Sugar", "Harry Styles"),
        ("Don't Stop Believin'", "Journey"),
        ("Hotel California", "Eagles"),
        ("Stairway to Heaven", "Led Zeppelin")
    ]
    
    # Test cases - songs that should NOT be filtered
    non_mainstream_test_cases = [
        ("Bohemian Rhapsody", "The Flaming Lips"),  # Cover version
        ("Love Me Not", "Ravyn Lenae"),  # Obscure song
        ("Coconut", "Harry Nilsson"),  # Classic but not mega-mainstream
        ("Jambalaya", "Hank Williams"),  # Classic country
        ("Strange Magnetism", "Foo Fighters")  # Deep cut
    ]
    
    print("🧪 TESTING MAINSTREAM DETECTION")
    print("=" * 50)
    
    print("\n✅ Songs that SHOULD be filtered as mainstream:")
    for title, artist in mainstream_test_cases:
        is_mainstream = scout._is_mainstream_song(title, artist)
        status = "✅ FILTERED" if is_mainstream else "❌ NOT FILTERED"
        print(f"  {title} by {artist}: {status}")
    
    print("\n🎵 Songs that should NOT be filtered:")
    for title, artist in non_mainstream_test_cases:
        is_mainstream = scout._is_mainstream_song(title, artist)
        status = "❌ INCORRECTLY FILTERED" if is_mainstream else "✅ ALLOWED"
        print(f"  {title} by {artist}: {status}")
    
    scout.close()

if __name__ == "__main__":
    test_mainstream_detection()
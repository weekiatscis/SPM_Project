#!/usr/bin/env python3
"""
Quick test to debug @mention detection
"""

import re

def test_mention_detection():
    """Test the mention detection regex"""
    print("🧪 Testing @Mention Detection")
    print("=" * 40)
    
    # Test cases
    test_comments = [
        "@zenia 2 gonna try the mentions",
        "Hey @john, can you review this?",
        "@jane @bob please check this out",
        "No mentions here",
        "@user1 @user2 @user3 multiple mentions",
        "@zenia2",  # No space after username
        "@zenia 2",  # With space
    ]
    
    mention_pattern = r'@([a-zA-Z][a-zA-Z0-9\s]*[a-zA-Z0-9]|[a-zA-Z])'
    
    for comment in test_comments:
        mentions = re.findall(mention_pattern, comment)
        print(f"Comment: '{comment}'")
        print(f"Mentions found: {mentions}")
        print()

if __name__ == "__main__":
    test_mention_detection()

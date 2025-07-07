#!/usr/bin/env python3
"""
Test script to verify token name extraction
"""

import logging
from monitor import OpenInterestMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_token_names():
    """Test token name extraction"""
    
    # Test single token
    print("Testing single token name extraction...")
    try:
        monitor = OpenInterestMonitor("mav.json")
        print(f"✅ Token names: {monitor.token_names}")
        print(f"✅ Token symbols: {monitor.token_list}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test multiple tokens
    print("\nTesting multiple token names extraction...")
    try:
        monitor2 = OpenInterestMonitor("tokens_config.json")
        print(f"✅ Token names: {monitor2.token_names}")
        print(f"✅ Token symbols: {monitor2.token_list}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_token_names() 
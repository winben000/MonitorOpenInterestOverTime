#!/usr/bin/env python3
"""
Test script to verify token loading from JSON files
"""

import json
import logging
from monitor import OpenInterestMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_token_loading():
    """Test loading tokens from different JSON formats"""
    
    # Test 1: Single symbol format (like bybit_sahara.json)
    print("Testing single symbol format...")
    try:
        monitor = OpenInterestMonitor("../Notional_PriceOverTime/bybit_sahara.json")
        print(f"✅ Successfully loaded tokens: {monitor.token_list}")
    except Exception as e:
        print(f"❌ Error loading single symbol: {e}")
    
    # Test 2: Create a test JSON with multiple symbols
    test_json = {
        "symbols": ["BTCUSDT", "ETHUSDT", "SAHARAUSDT"]
    }
    
    with open("test_symbols.json", "w") as f:
        json.dump(test_json, f, indent=2)
    
    print("\nTesting multiple symbols format...")
    try:
        monitor2 = OpenInterestMonitor("test_symbols.json")
        print(f"✅ Successfully loaded tokens: {monitor2.token_list}")
    except Exception as e:
        print(f"❌ Error loading multiple symbols: {e}")
    
    # Test 3: Default behavior (no JSON file)
    print("\nTesting default behavior...")
    try:
        monitor3 = OpenInterestMonitor()
        print(f"✅ Default tokens: {monitor3.token_list}")
    except Exception as e:
        print(f"❌ Error with default behavior: {e}")

if __name__ == "__main__":
    test_token_loading() 
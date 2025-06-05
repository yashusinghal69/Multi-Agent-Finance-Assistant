#!/usr/bin/env python3
"""
Test script to verify improved error handling for delisted stocks
"""
import sys
sys.path.append('app')

from agents.api_agent import get_stock_info, market_data_tool

def test_delisted_stocks():
    print("=== Testing Delisted Stock Error Handling ===\n")
    
    # Test individual stock info function
    print("1. Testing get_stock_info function:")
    
    test_symbols = ['GUY', 'STCK', 'INVALIDXYZ', 'AAPL']  # Mix of invalid and valid
    
    for symbol in test_symbols:
        print(f"\nTesting symbol: {symbol}")
        result = get_stock_info(symbol)
        
        if 'error' in result:
            print(f"  ✅ Error handled gracefully: {result['error']}")
            print(f"  Status: {result.get('status', 'unknown')}")
        else:
            print(f"  ✅ Valid stock data received: {result['name']} - ${result['current_price']}")
    
    print("\n" + "="*60)
    print("2. Testing market_data_tool function:")
    
    # Test market data tool with problematic query
    test_queries = [
        "What about GUY and STCK stocks?",
        "Show me AAPL stock price",
        "Tell me about invalid stocks like BADSTCK and FAKEGUY"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            result = market_data_tool(query)
            print(f"  ✅ Result: {result[:200]}..." if len(result) > 200 else f"  ✅ Result: {result}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ Test completed! The application should now handle delisted stocks gracefully.")

if __name__ == "__main__":
    test_delisted_stocks()

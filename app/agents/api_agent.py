import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

def get_stock_info(symbol: str) -> Dict[str, Any]:
    """
    Get basic stock information for a given symbol
    """
    try:
        stock = yf.Ticker(symbol)
        
        # Try to get current data from history first
        hist = stock.history(period="1d")
        
        if hist.empty:
            # Try longer period
            hist = stock.history(period="5d")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Open'].iloc[-1] 
            volume = hist['Volume'].iloc[-1]
        else:
            # No historical data available - stock might be delisted or invalid
            return {
                "symbol": symbol,
                "error": f"No price data available for {symbol}. Stock may be delisted or invalid.",
                "status": "delisted_or_invalid"
            }
        
        # Try to get info
        info = stock.info if hasattr(stock, 'info') else {}
        
        # Validate that we have meaningful data
        if current_price <= 0 or pd.isna(current_price):
            return {
                "symbol": symbol,
                "error": f"Invalid price data for {symbol}. Stock may be delisted.",
                "status": "invalid_data"
            }
        
        # Calculate change
        change_percent = 0
        if previous_close > 0:
            change_percent = round(((current_price - previous_close) / previous_close) * 100, 2)
        
        return {
            "symbol": symbol,
            "name": info.get("longName", f"{symbol} Inc."),
            "current_price": round(float(current_price), 2),
            "previous_close": round(float(previous_close), 2) if previous_close > 0 else info.get("previousClose", 0),
            "change_percent": change_percent,
            "market_cap": info.get("marketCap", "N/A"),
            "volume": int(volume) if volume > 0 else info.get("volume", 0),
            "sector": info.get("sector", "Technology"),
            "industry": info.get("industry", "Consumer Electronics"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active"
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "error": f"Error fetching data for {symbol}: {str(e)}",
            "status": "error"
        }

def get_portfolio_data(symbols: List[str]) -> List[Dict[str, Any]]:
    """
    Get portfolio data for multiple symbols
    """
    portfolio_data = []
    valid_stocks = []
    invalid_stocks = []
    
    for symbol in symbols:
        data = get_stock_info(symbol)
        
        if "error" in data or data.get("status") in ["delisted_or_invalid", "invalid_data", "error"]:
            invalid_stocks.append({"symbol": symbol, "reason": data.get("error", "Unknown error")})
        else:
            portfolio_data.append(data)
            valid_stocks.append(symbol)
    
    # Add summary information
    result = {
        "valid_stocks": portfolio_data,
        "valid_count": len(valid_stocks),
        "invalid_stocks": invalid_stocks,
        "invalid_count": len(invalid_stocks),
        "total_requested": len(symbols)
    }
    
    return [result]  # Return as list to maintain compatibility

def get_market_overview() -> Dict[str, Any]:
    """
    Get major market indices overview
    """
    indices = ["^GSPC", "^DJI", "^IXIC", "^RUT"]  # S&P 500, Dow, NASDAQ, Russell 2000
    index_names = ["S&P 500", "Dow Jones", "NASDAQ", "Russell 2000"]
    
    market_data = {}
    
    for i, symbol in enumerate(indices):
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="2d")
            
            if not hist.empty:
                current = float(hist['Close'].iloc[-1])
                previous = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
                change_pct = round(((current - previous) / previous) * 100, 2)
                
                market_data[index_names[i]] = {
                    "current": current,
                    "change_percent": change_pct,
                    "volume": int(hist['Volume'].iloc[-1]) if not pd.isna(hist['Volume'].iloc[-1]) else 0
                }
        except Exception as e:
            market_data[index_names[i]] = {"error": str(e)}
    
    return market_data

def get_sector_performance() -> Dict[str, Any]:
    """
    Get sector ETF performance
    """
    sector_etfs = {
        "Technology": "XLK",
        "Healthcare": "XLV", 
        "Financials": "XLF",
        "Energy": "XLE",
        "Consumer Discretionary": "XLY"
    }
    
    sector_data = {}
    
    for sector, etf in sector_etfs.items():
        try:
            stock = yf.Ticker(etf)
            hist = stock.history(period="2d")
            
            if not hist.empty:
                current = float(hist['Close'].iloc[-1])
                previous = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
                change_pct = round(((current - previous) / previous) * 100, 2)
                
                sector_data[sector] = {
                    "etf": etf,
                    "current": current,
                    "change_percent": change_pct
                }
        except Exception as e:
            sector_data[sector] = {"error": str(e)}
    
    return sector_data

def analyze_portfolio_risk(symbols: List[str], weights: List[float] = None) -> Dict[str, Any]:
    """
    Simple portfolio risk analysis
    """
    if weights is None:
        weights = [1/len(symbols)] * len(symbols)
    
    try:
        # Get historical data for portfolio
        portfolio_data = []
        total_value = 0
        valid_stocks = 0
        invalid_stocks = []
        
        for i, symbol in enumerate(symbols):
            stock_data = get_stock_info(symbol)
            if "error" not in stock_data and stock_data.get("status") == "active":
                weighted_value = stock_data["current_price"] * weights[i]
                total_value += weighted_value
                portfolio_data.append({
                    "symbol": symbol,
                    "weight": weights[i],
                    "current_price": stock_data["current_price"],
                    "weighted_value": weighted_value,
                    "sector": stock_data["sector"]
                })
                valid_stocks += 1
            else:
                invalid_stocks.append({
                    "symbol": symbol,
                    "error": stock_data.get("error", "Unknown error")
                })
        
        if valid_stocks == 0:
            return {
                "error": "No valid stocks found for portfolio analysis",
                "invalid_stocks": invalid_stocks
            }
        
        # Calculate sector allocation
        sector_allocation = {}
        for stock in portfolio_data:
            sector = stock["sector"]
            if sector in sector_allocation:
                sector_allocation[sector] += stock["weight"]
            else:
                sector_allocation[sector] = stock["weight"]
        
        return {
            "total_portfolio_value": total_value,
            "valid_stocks": portfolio_data,
            "valid_stock_count": valid_stocks,
            "invalid_stocks": invalid_stocks,
            "invalid_stock_count": len(invalid_stocks),
            "sector_allocation": sector_allocation,
            "risk_level": "Medium" if valid_stocks > 5 else "High"  # Simple risk assessment
        }
        
    except Exception as e:
        return {"error": f"Portfolio analysis error: {str(e)}"}

# Tool functions for LangGraph integration
def market_data_tool(query: str) -> str:
    """
    Tool to get market data based on query
    """
    query_lower = query.lower()
    
    # Stock name to symbol mapping
    stock_mapping = {
        "apple": "AAPL",
        "microsoft": "MSFT", 
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "tesla": "TSLA",
        "nvidia": "NVDA",
        "amazon": "AMZN",
        "meta": "META",
        "facebook": "META",
        "netflix": "NFLX",
        "intel": "INTC",
        "amd": "AMD",
        "oracle": "ORCL",
        "salesforce": "CRM",        "adobe": "ADBE"
    }
    
    if "portfolio" in query_lower or "risk" in query_lower:
        # Default tech portfolio for demo
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        risk_data = analyze_portfolio_risk(symbols)
        return f"Portfolio Risk Analysis: {risk_data}"
    
    elif "market" in query_lower or "indices" in query_lower:
        market_data = get_market_overview()
        return f"Market Overview: {market_data}"
    
    elif "sector" in query_lower:
        sector_data = get_sector_performance()
        return f"Sector Performance: {sector_data}"
    
    else:
        # Extract stock symbols from query - be more selective
        words = query.upper().split()
        
        # Expanded exclude words list to avoid false positives
        exclude_words = {"THE", "IS", "OF", "AND", "OR", "TO", "IN", "ON", "AT", "FOR", 
                        "WITH", "BY", "FROM", "UP", "ABOUT", "INTO", "THROUGH", "DURING",
                        "BEFORE", "AFTER", "ABOVE", "BELOW", "BETWEEN", "STOCK", "STOCKS",
                        "TODAY", "PRICE", "WHAT", "HOW", "WHERE", "WHEN", "WHY", "WHO",
                        "THIS", "THAT", "THESE", "THOSE", "SOME", "ANY", "ALL", "EACH",
                        "EVERY", "BOTH", "EITHER", "NEITHER", "MUCH", "MANY", "MORE",
                        "MOST", "SUCH", "WHAT", "WHICH", "THAT", "WHO", "WHOM", "WHOSE",
                        "GUY", "GUYS", "LIKE", "JUST", "ONLY", "ALSO", "EVEN", "STILL",
                        "VERY", "QUITE", "RATHER", "PRETTY", "REAL", "REALLY", "TRUE",
                        "FALSE", "GOOD", "BAD", "BEST", "WORST", "FIRST", "LAST", "NEXT",
                        "SAME", "OTHER", "BOTH", "FEW", "LITTLE", "LESS", "LEAST", "MUCH",
                        "MORE", "MOST", "ENOUGH", "SEVERAL", "MANY", "STCK", "STOCK"}
        
        # More strict filtering - only consider words that could realistically be stock symbols
        potential_symbols = []
        for word in words:
            if (len(word) >= 2 and len(word) <= 5 and 
                word.isalpha() and 
                word not in exclude_words and
                word.isupper()):  # Only consider if already uppercase or explicitly formatted as symbol
                potential_symbols.append(word)
        
        # Also check for company names
        company_symbols = []
        for company, symbol in stock_mapping.items():
            if company in query_lower:
                company_symbols.append(symbol)
        
        # Look for explicit symbol patterns (e.g., $AAPL, AAPL:, etc.)
        import re
        symbol_patterns = re.findall(r'\$([A-Z]{1,5})\b', query.upper())
        explicit_symbols = [symbol for symbol in symbol_patterns if symbol not in exclude_words]
        
        # Combine found symbols, prioritizing explicit symbols and company names
        all_symbols = list(set(explicit_symbols + company_symbols + potential_symbols))
        
        if all_symbols:
            stock_data = get_portfolio_data(all_symbols[:3])  # Limit to 3 stocks
            return f"Stock Data: {stock_data}"
        else:
            # If no specific stock found but query mentions stock/price, show popular stocks
            if any(word in query_lower for word in ["stock", "price", "shares", "ticker"]):
                default_stocks = ["AAPL", "MSFT", "GOOGL"]
                stock_data = get_portfolio_data(default_stocks)
                return f"Top Tech Stocks: {stock_data}"
            else:
                market_data = get_market_overview()
                return f"Market Overview: {market_data}"

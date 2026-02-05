#!/usr/bin/env python3
"""
Financial Data Fetcher Script
Fetches financial data for public companies using Yahoo Finance.

Usage:
    python fetch_financials.py --ticker "AAPL"
    python fetch_financials.py --company "Apple Inc"
    echo '{"ticker": "AAPL"}' | python fetch_financials.py --stdin

Output: JSON with company info, stock price, financials, key metrics
"""

import argparse
import json
import sys
import re
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    print("Error: yfinance not installed. Run: pip install yfinance", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None


def search_ticker(company_name: str) -> dict:
    """
    Search for a stock ticker by company name using Yahoo Finance search.

    Returns:
        Dict with ticker, name, and exchange if found, else None
    """
    if not requests:
        return None

    try:
        # Yahoo Finance search API
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            "q": company_name,
            "quotesCount": 10,
            "newsCount": 0,
            "enableFuzzyQuery": True,
            "quotesQueryId": "tss_match_phrase_query"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        quotes = data.get("quotes", [])

        if not quotes:
            return None

        # Only accept EQUITY type - skip crypto, mutual funds, ETFs, etc.
        company_lower = company_name.lower()
        for quote in quotes:
            quote_type = quote.get("quoteType", "")
            symbol = quote.get("symbol", "")
            name = (quote.get("shortname") or quote.get("longname", "")).lower()

            # Only accept stocks (equities)
            if quote_type != "EQUITY":
                continue

            # Check if company name appears in the result name
            # This helps avoid false positives
            name_words = set(re.findall(r'\w+', name))
            search_words = set(re.findall(r'\w+', company_lower))

            # At least one significant word should match
            if search_words & name_words:
                return {
                    "ticker": symbol,
                    "name": quote.get("shortname") or quote.get("longname", ""),
                    "exchange": quote.get("exchange", ""),
                    "type": quote_type
                }

        # No good equity match found - company is likely private
        return None

    except Exception as e:
        print(f"Ticker search error: {e}", file=sys.stderr)
        return None


def format_number(value) -> str:
    """Format large numbers for readability."""
    if value is None:
        return "N/A"
    if isinstance(value, str):
        return value

    try:
        value = float(value)
        if abs(value) >= 1e12:
            return f"${value/1e12:.2f}T"
        elif abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"
    except:
        return str(value)


def safe_get(info: dict, key: str, default=None):
    """Safely get a value from dict."""
    try:
        value = info.get(key, default)
        return value if value is not None else default
    except:
        return default


def fetch_financials(ticker: str) -> dict:
    """
    Fetch financial data for a public company.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "GOOGL")

    Returns:
        Dict with company info, stock data, and financials
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Check if valid ticker
        if not info or info.get("regularMarketPrice") is None:
            return {
                "success": False,
                "ticker": ticker,
                "error": "Ticker not found or no data available"
            }

        # Basic company info
        company_info = {
            "name": safe_get(info, "longName", safe_get(info, "shortName", ticker)),
            "ticker": ticker.upper(),
            "sector": safe_get(info, "sector", "N/A"),
            "industry": safe_get(info, "industry", "N/A"),
            "country": safe_get(info, "country", "N/A"),
            "website": safe_get(info, "website", "N/A"),
            "employees": safe_get(info, "fullTimeEmployees", "N/A"),
            "description": safe_get(info, "longBusinessSummary", "")[:1000],
        }

        # Stock price data
        stock_data = {
            "current_price": safe_get(info, "regularMarketPrice"),
            "previous_close": safe_get(info, "previousClose"),
            "open": safe_get(info, "regularMarketOpen"),
            "day_high": safe_get(info, "dayHigh"),
            "day_low": safe_get(info, "dayLow"),
            "52_week_high": safe_get(info, "fiftyTwoWeekHigh"),
            "52_week_low": safe_get(info, "fiftyTwoWeekLow"),
            "volume": safe_get(info, "regularMarketVolume"),
            "avg_volume": safe_get(info, "averageVolume"),
            "currency": safe_get(info, "currency", "USD"),
        }

        # Key financial metrics
        financials = {
            "market_cap": safe_get(info, "marketCap"),
            "market_cap_formatted": format_number(safe_get(info, "marketCap")),
            "enterprise_value": safe_get(info, "enterpriseValue"),
            "revenue": safe_get(info, "totalRevenue"),
            "revenue_formatted": format_number(safe_get(info, "totalRevenue")),
            "gross_profit": safe_get(info, "grossProfits"),
            "ebitda": safe_get(info, "ebitda"),
            "net_income": safe_get(info, "netIncomeToCommon"),
            "profit_margin": safe_get(info, "profitMargins"),
            "operating_margin": safe_get(info, "operatingMargins"),
            "revenue_growth": safe_get(info, "revenueGrowth"),
            "earnings_growth": safe_get(info, "earningsGrowth"),
        }

        # Valuation metrics
        valuation = {
            "pe_ratio": safe_get(info, "trailingPE"),
            "forward_pe": safe_get(info, "forwardPE"),
            "peg_ratio": safe_get(info, "pegRatio"),
            "price_to_book": safe_get(info, "priceToBook"),
            "price_to_sales": safe_get(info, "priceToSalesTrailing12Months"),
            "ev_to_revenue": safe_get(info, "enterpriseToRevenue"),
            "ev_to_ebitda": safe_get(info, "enterpriseToEbitda"),
        }

        # Dividend info
        dividends = {
            "dividend_rate": safe_get(info, "dividendRate"),
            "dividend_yield": safe_get(info, "dividendYield"),
            "payout_ratio": safe_get(info, "payoutRatio"),
            "ex_dividend_date": safe_get(info, "exDividendDate"),
        }

        # Analyst recommendations
        recommendations = {
            "target_mean_price": safe_get(info, "targetMeanPrice"),
            "target_high_price": safe_get(info, "targetHighPrice"),
            "target_low_price": safe_get(info, "targetLowPrice"),
            "recommendation": safe_get(info, "recommendationKey"),
            "num_analysts": safe_get(info, "numberOfAnalystOpinions"),
        }

        return {
            "success": True,
            "ticker": ticker.upper(),
            "company": company_info,
            "stock": stock_data,
            "financials": financials,
            "valuation": valuation,
            "dividends": dividends,
            "recommendations": recommendations,
            "fetched_at": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "ticker": ticker,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Fetch financial data for a company")
    parser.add_argument("--ticker", "-t", type=str, help="Stock ticker symbol")
    parser.add_argument("--company", "-c", type=str, help="Company name (will search for ticker)")
    parser.add_argument("--stdin", action="store_true", help="Read JSON input from stdin")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")

    args = parser.parse_args()

    ticker = None
    company_name = None
    searched_ticker = None

    # Get input
    if args.stdin:
        input_data = json.load(sys.stdin)
        ticker = input_data.get("ticker", "")
        company_name = input_data.get("company", "")
    else:
        ticker = args.ticker
        company_name = args.company

    # If company name provided, search for ticker
    if company_name and not ticker:
        print(f"Searching for ticker: {company_name}", file=sys.stderr)
        search_result = search_ticker(company_name)
        if search_result:
            ticker = search_result["ticker"]
            searched_ticker = search_result
            print(f"Found ticker: {ticker} ({search_result.get('name', '')})", file=sys.stderr)
        else:
            print(f"No ticker found for: {company_name}", file=sys.stderr)

    if not ticker:
        result = {
            "success": False,
            "company_name": company_name,
            "error": "No ticker found - company may be private or not publicly traded",
            "note": "Financial data is only available for publicly traded companies with stock tickers"
        }
    else:
        # Fetch data
        result = fetch_financials(ticker)

        # Add search info if we searched
        if searched_ticker:
            result["searched_from"] = company_name
            result["ticker_search"] = searched_ticker

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit with error if fetch failed
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()

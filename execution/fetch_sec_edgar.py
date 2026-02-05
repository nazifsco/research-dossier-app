#!/usr/bin/env python3
"""
SEC EDGAR Fetcher Script
Fetches company filings and data from SEC EDGAR (free, no key required).

Usage:
    python fetch_sec_edgar.py --company "Apple"
    python fetch_sec_edgar.py --cik "0000320193"
    python fetch_sec_edgar.py --ticker "AAPL"

Output: JSON with company info, recent filings, and financial highlights

Note: Only works for US public companies that file with the SEC.
"""

import argparse
import json
import sys
import re
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


# SEC requires a User-Agent header with contact info
HEADERS = {
    "User-Agent": "ResearchAgent/1.0 (contact@example.com)",
    "Accept": "application/json"
}

SEC_BASE = "https://data.sec.gov"
SEC_EFTS = "https://efts.sec.gov/LATEST/search-index"


def search_company(query: str) -> list:
    """Search for companies by name."""
    url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        "action": "getcompany",
        "company": query,
        "type": "",
        "dateb": "",
        "owner": "include",
        "count": 10,
        "output": "atom"
    }

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()

        # Parse the Atom XML response (simplified)
        results = []
        # Extract company entries using regex (avoid XML parsing dependency)
        entries = re.findall(r'<entry>(.*?)</entry>', response.text, re.DOTALL)

        for entry in entries[:5]:
            title_match = re.search(r'<title>([^<]+)</title>', entry)
            cik_match = re.search(r'CIK=(\d+)', entry)

            if title_match:
                title = title_match.group(1)
                # Parse "COMPANY NAME (CIK)" format
                name_match = re.match(r'(.+?)\s*\(CIK', title)
                results.append({
                    "name": name_match.group(1).strip() if name_match else title,
                    "cik": cik_match.group(1) if cik_match else None
                })

        return results
    except Exception as e:
        print(f"SEC search error: {e}", file=sys.stderr)
        return []


def get_cik_from_ticker(ticker: str) -> str:
    """Look up CIK from ticker symbol."""
    try:
        url = f"{SEC_BASE}/submissions/CIK{ticker.upper()}.json"
        response = requests.get(url, headers=HEADERS, timeout=30)

        if response.status_code == 200:
            data = response.json()
            return data.get("cik", "")
    except:
        pass

    # Try the ticker mapping file
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        ticker_upper = ticker.upper()
        for entry in data.values():
            if entry.get("ticker") == ticker_upper:
                return str(entry.get("cik_str", "")).zfill(10)
    except Exception as e:
        print(f"Ticker lookup error: {e}", file=sys.stderr)

    return ""


def get_company_info(cik: str) -> dict:
    """Get company information from SEC."""
    # Normalize CIK to 10 digits
    cik_padded = cik.zfill(10)

    try:
        url = f"{SEC_BASE}/submissions/CIK{cik_padded}.json"
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Extract recent filings
        filings = []
        recent = data.get("filings", {}).get("recent", {})
        if recent:
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            descriptions = recent.get("primaryDocument", [])
            accessions = recent.get("accessionNumber", [])

            for i in range(min(20, len(forms))):
                filings.append({
                    "form": forms[i] if i < len(forms) else "",
                    "date": dates[i] if i < len(dates) else "",
                    "document": descriptions[i] if i < len(descriptions) else "",
                    "accession": accessions[i] if i < len(accessions) else ""
                })

        # Filter for important filings
        important_forms = ["10-K", "10-Q", "8-K", "DEF 14A", "S-1", "424B"]
        important_filings = [f for f in filings if any(form in f["form"] for form in important_forms)]

        return {
            "cik": data.get("cik", cik),
            "name": data.get("name", ""),
            "ticker": data.get("tickers", [""])[0] if data.get("tickers") else "",
            "sic": data.get("sic", ""),
            "sic_description": data.get("sicDescription", ""),
            "state": data.get("stateOfIncorporation", ""),
            "fiscal_year_end": data.get("fiscalYearEnd", ""),
            "business_address": data.get("addresses", {}).get("business", {}),
            "mailing_address": data.get("addresses", {}).get("mailing", {}),
            "phone": data.get("phone", ""),
            "website": data.get("website", ""),
            "filings_count": len(filings),
            "recent_filings": important_filings[:10],
            "all_tickers": data.get("tickers", []),
            "exchanges": data.get("exchanges", [])
        }
    except Exception as e:
        print(f"SEC company info error: {e}", file=sys.stderr)
        return {"error": str(e)}


def get_company_facts(cik: str) -> dict:
    """Get company financial facts (XBRL data)."""
    cik_padded = cik.zfill(10)

    try:
        url = f"{SEC_BASE}/api/xbrl/companyfacts/CIK{cik_padded}.json"
        response = requests.get(url, headers=HEADERS, timeout=30)

        if response.status_code != 200:
            return {}

        data = response.json()

        facts = {}
        us_gaap = data.get("facts", {}).get("us-gaap", {})

        # Extract key financial metrics
        key_metrics = [
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "NetIncomeLoss",
            "EarningsPerShareBasic",
            "Assets",
            "Liabilities",
            "StockholdersEquity",
            "CashAndCashEquivalentsAtCarryingValue",
            "CommonStockSharesOutstanding"
        ]

        for metric in key_metrics:
            if metric in us_gaap:
                units = us_gaap[metric].get("units", {})
                # Get USD values if available
                usd_values = units.get("USD", units.get("shares", []))
                if usd_values:
                    # Get most recent annual (10-K) value
                    annual = [v for v in usd_values if v.get("form") == "10-K"]
                    if annual:
                        latest = sorted(annual, key=lambda x: x.get("end", ""), reverse=True)[0]
                        facts[metric] = {
                            "value": latest.get("val"),
                            "end_date": latest.get("end"),
                            "form": latest.get("form")
                        }

        return facts
    except Exception as e:
        print(f"SEC facts error: {e}", file=sys.stderr)
        return {}


def fetch_sec_data(company: str = None, cik: str = None, ticker: str = None) -> dict:
    """
    Fetch SEC EDGAR data for a company.

    Args:
        company: Company name to search
        cik: Direct CIK number
        ticker: Stock ticker symbol

    Returns:
        Dict with SEC data
    """
    # Resolve CIK
    resolved_cik = None

    if cik:
        resolved_cik = cik.replace("CIK", "").strip()
    elif ticker:
        resolved_cik = get_cik_from_ticker(ticker)
        if not resolved_cik:
            return {
                "success": False,
                "query": ticker,
                "error": f"Could not find CIK for ticker: {ticker}"
            }
    elif company:
        results = search_company(company)
        if results and results[0].get("cik"):
            resolved_cik = results[0]["cik"]
        else:
            return {
                "success": False,
                "query": company,
                "error": f"Company not found in SEC database: {company}"
            }

    if not resolved_cik:
        return {
            "success": False,
            "error": "No company identifier provided"
        }

    # Get company info
    info = get_company_info(resolved_cik)
    if "error" in info:
        return {
            "success": False,
            "cik": resolved_cik,
            "error": info["error"]
        }

    # Get financial facts
    time.sleep(0.5)  # Rate limiting
    facts = get_company_facts(resolved_cik)

    return {
        "success": True,
        "cik": resolved_cik,
        "company_info": info,
        "financial_facts": facts,
        "source": "sec_edgar",
        "note": "Data from SEC EDGAR. Only available for US public companies."
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch SEC EDGAR data")
    parser.add_argument("--company", "-c", type=str, help="Company name to search")
    parser.add_argument("--cik", type=str, help="CIK number")
    parser.add_argument("--ticker", "-t", type=str, help="Stock ticker symbol")
    parser.add_argument("--output", "-o", type=str, help="Output file")

    args = parser.parse_args()

    if not any([args.company, args.cik, args.ticker]):
        print("Error: Provide --company, --cik, or --ticker", file=sys.stderr)
        sys.exit(1)

    result = fetch_sec_data(
        company=args.company,
        cik=args.cik,
        ticker=args.ticker
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Web Search & Acquisition Module

This module searches for financial assistance grants using the Tavily search API.
It constructs targeted queries that consider both disease type and income eligibility,
then extracts and standardizes the results for downstream analysis.

The Hunter is the first step in the grant-finding pipeline, responsible for acquiring
raw data from nonprofit and foundation databases.

Environment Requirements:
  - TAVILY_API_KEY: API key for Tavily search service (set in .env)

Author: DuckDuckCode
"""

import os
from tavily import TavilyClient

# Initialize Tavily search client with API key from environment
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY not set. Add it to .env or the environment.")

client = TavilyClient(api_key=TAVILY_API_KEY)


def hunt_for_grants(disease_name, fpl_pct):
    """
    Search for financial assistance grants related to a disease and income level.
    
    Constructs a targeted search query that looks for nonprofit and foundation grants
    matching the patient's disease and income eligibility. Filters out PDF-only results
    which are less useful for initial discovery.
    
    Args:
        disease_name (str): Full name of the disease (e.g., "Heart Disease and Stroke").
                           This is typically retrieved from health_disorder_codes dictionary.
        fpl_pct (float): Federal Poverty Level percentage (e.g., 125.5 = 125.5% of FPL).
                        Used to tailor search for low-income assistance programs.
    
    Returns:
        list: List of grant dictionaries, each containing:
            - name (str): Grant or program name
            - url (str): Website URL for the grant
            - description (str): Full grant description from search result
            - short_description (str): Truncated description (first 200 chars)
            - type (str): Grant type (usually "Nonprofit")
            - deadline (str): Deadline info ("Check Site" if not found)
            - income_focus (str): Whether search targeted "low income" or general "financial assistance"
    
    Examples:
        >>> grants = hunt_for_grants("Diabetes", 145.0)
        >>> len(grants) > 0
        True
        >>> 'name' in grants[0]
        True
    
    Note:
        - Searches restricted to .org domain for nonprofit/foundation sites
        - Filters results to look for 2026 open grants
        - Excludes PDF-only results for better user experience
        - Returns up to 10 results from Tavily advanced search
    """
    # Tailor search strategy based on income eligibility
    # Lower FPL = more eligible for low-income assistance programs
    income_tag = "low income financial assistance" if fpl_pct <= 150 else "financial assistance"
    
    # Construct search query targeting nonprofit sites with disease and income keywords
    # "open 2026" ensures we find currently accepting applications
    query = f'site:.org "{disease_name}" {income_tag} grants open 2026'
    
    # Execute advanced search through Tavily
    response = client.search(query, search_depth="advanced", max_results=10)
    results = response.get('results', [])
    
    found_awards = []
    for item in results:
        # Skip PDF-only results as they're less accessible for users
        url = item.get('url', '').lower()
        title = item.get('title', '').lower()
        if '.pdf' in url or 'pdf' in title:
            continue
        
        # Standardize grant information for downstream processing
        found_awards.append({
            "name": item['title'],
            "url": item['url'],
            "description": item['content'],
            "short_description": item['content'][:200] if len(item['content']) > 200 else item['content'],
            "type": "Nonprofit",
            "deadline": "Check Site",
            "income_focus": income_tag
        })
    
    return found_awards
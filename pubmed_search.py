#!/usr/bin/env python3
"""
PubMed search module for retrieving hernia surgery research articles.
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class PubMedSearcher:
    """Handles PubMed/NCBI API interactions."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self):
        self.email = "research@example.com"
        self.api_key = None
    
    def run_weekly_search(self, max_results: int = 50) -> List[Dict]:
        """
        Search PubMed for recent hernia surgery articles.
        
        Args:
            max_results: Maximum number of articles to retrieve
            
        Returns:
            List of article dictionaries with pubmed metadata
        """
        logger.info(f"Searching PubMed for hernia surgery articles...")
        
        try:
            # Build search query for hernia surgery
            search_query = "hernia surgery"
            
            # Get PMIDs using esearch
            search_params = {
                "db": "pubmed",
                "term": search_query,
                "retmax": max_results,
                "rettype": "json",
                "email": self.email
            }
            
            if self.api_key:
                search_params["api_key"] = self.api_key
            
            search_url = f"{self.BASE_URL}/esearch.fcgi"
            response = requests.get(search_url, params=search_params, timeout=10)
            response.raise_for_status()
            
            search_data = response.json()
            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not pmids:
                logger.warning("No PMIDs found")
                return []
            
            logger.info(f"Found {len(pmids)} PMIDs, fetching details...")
            
            # Get article summaries using esummary
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "rettype": "json",
                "email": self.email
            }
            
            if self.api_key:
                fetch_params["api_key"] = self.api_key
            
            fetch_url = f"{self.BASE_URL}/esummary.fcgi"
            response = requests.get(fetch_url, params=fetch_params, timeout=10)
            response.raise_for_status()
            
            fetch_data = response.json()
            articles = []
            
            # Parse article data
            for uid, article_data in fetch_data.get("result", {}).items():
                if uid == "uids":
                    continue
                
                article = {
                    "pmid": uid,
                    "title": article_data.get("title", ""),
                    "authors": article_data.get("authors", []),
                    "pubdate": article_data.get("pubdate", ""),
                    "journal": article_data.get("fulljournalname", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                }
                articles.append(article)
            
            logger.info(f"Successfully retrieved {len(articles)} articles")
            return articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching PubMed data: {e}")
            return []
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing PubMed response: {e}")
            return []


def format_articles_for_email(articles: List[Dict]) -> str:
    """
    Format articles for display and email.
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        Formatted string representation
    """
    if not articles:
        return "No articles found."
    
    formatted = f"Found {len(articles)} articles:\n\n"
    
    for i, article in enumerate(articles, 1):
        formatted += f"{i}. {article.get('title', 'No title')}\n"
        formatted += f"   Journal: {article.get('journal', 'Unknown')}\n"
        formatted += f"   Date: {article.get('pubdate', 'Unknown')}\n"
        formatted += f"   URL: {article.get('url', '')}\n"
        
        authors = article.get('authors', [])
        if authors:
            author_list = ", ".join([a.get('name', 'Unknown') for a in authors[:3]])
            if len(authors) > 3:
                author_list += f", +{len(authors) - 3} more"
            formatted += f"   Authors: {author_list}\n"
        
        formatted += "\n"
    
    return formatted


def save_results(articles: List[Dict], filename: str) -> None:
    """
    Save search results to JSON file.
    
    Args:
        articles: List of article dictionaries
        filename: Output filename
    """
    try:
        with open(filename, 'w') as f:
            json.dump(articles, f, indent=2, default=str)
        logger.info(f"Results saved to {filename}")
    except IOError as e:
        logger.error(f"Error saving results to {filename}: {e}")

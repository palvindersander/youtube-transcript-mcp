#!/usr/bin/env python3
"""
Search API client for the YouTube Transcript fact-checking feature.
This module provides functionality to search the web for information
to verify claims made in YouTube videos.
"""

import os
import json
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("search_api")

class SearchAPIError(Exception):
    """Exception raised when search API request fails."""
    pass

class SearchAPIClient:
    """Client for web search API integration."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the search API client.
        
        Args:
            api_key: API key for the search service. If None, will try to load from environment variable.
        """
        self.api_key = api_key or os.environ.get("SEARCH_API_KEY")
        if not self.api_key:
            logger.warning("No Search API key provided. Searches will not work.")
        
        # Configurable endpoints - default to Serper.dev
        self.search_endpoint = "https://google.serper.dev/search"
    
    async def search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Search the web for information about a claim.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            Structured search results
            
        Raises:
            SearchAPIError: If the search fails
        """
        if not self.api_key:
            raise SearchAPIError("No Search API key configured")
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.search_endpoint,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise SearchAPIError(f"Search API returned {response.status}: {error_text}")
                    
                    search_results = await response.json()
                    return self._format_search_results(search_results, query)
        
        except aiohttp.ClientError as e:
            raise SearchAPIError(f"Search request failed: {str(e)}")
        
    def _format_search_results(self, raw_results: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format raw search results into a structured format for fact checking.
        
        Args:
            raw_results: Raw response from the search API
            query: The original search query
            
        Returns:
            Structured search results
        """
        formatted_results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": []
        }
        
        # Extract organic search results
        if "organic" in raw_results:
            for result in raw_results["organic"]:
                formatted_result = {
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "source": result.get("source"),
                    "published_date": result.get("date")
                }
                formatted_results["results"].append(formatted_result)
        
        # Extract knowledge graph if available
        if "knowledgeGraph" in raw_results:
            kg = raw_results["knowledgeGraph"]
            formatted_results["knowledge_graph"] = {
                "title": kg.get("title"),
                "type": kg.get("type"),
                "description": kg.get("description"),
                "attributes": kg.get("attributes", {})
            }
        
        return formatted_results
    
    async def search_for_claim_verification(self, claim: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Search for information to verify a specific claim.
        
        Args:
            claim: The claim to verify
            context: Optional context to help with the search
            
        Returns:
            Structured search results for fact checking
        """
        # Create a focused search query for fact-checking
        query = f"fact check \"{claim}\""
        
        if context:
            # Add context to the search query
            query += f" {context}"
        
        # Perform the search
        results = await self.search(query)
        
        # Add a second search for direct information about the claim
        direct_query = claim
        direct_results = await self.search(direct_query)
        
        # Combine results
        combined_results = {
            "claim": claim,
            "context": context,
            "fact_check_results": results,
            "information_results": direct_results
        }
        
        return combined_results
        
# Helper function to create a new instance with default settings
def create_search_client(api_key: Optional[str] = None) -> SearchAPIClient:
    """Create a new search client instance with default settings.
    
    Args:
        api_key: Optional API key (will use env variable if not provided)
        
    Returns:
        Configured SearchAPIClient instance
    """
    return SearchAPIClient(api_key) 
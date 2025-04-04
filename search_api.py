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

# Try to import the API key from config file
try:
    from config import SEARCH_API_KEY as CONFIG_API_KEY
except ImportError:
    CONFIG_API_KEY = None

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
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        """Initialize the search API client.
        
        Args:
            api_key: API key for the search service. If None, will try to load from config or environment variable.
            mock_mode: If True, will use mock responses instead of making actual API calls when no API key is available.
        """
        # Try API key from params, then config file, then environment variable
        self.api_key = api_key or CONFIG_API_KEY or os.environ.get("SEARCH_API_KEY")
        self.mock_mode = mock_mode
        
        if not self.api_key and not self.mock_mode:
            logger.warning("No Search API key provided. Searches will not work unless mock_mode is enabled.")
        elif not self.api_key and self.mock_mode:
            logger.info("No Search API key provided. Using mock responses for searches.")
        
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
            SearchAPIError: If the search fails and mock_mode is disabled
        """
        if not self.api_key:
            if self.mock_mode:
                # Generate a mock response for testing
                return self._generate_mock_results(query, num_results)
            else:
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
    
    def _generate_mock_results(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Generate mock search results for testing purposes.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            Mock search results in the same format as real results
        """
        # Construct a basic mock response
        mock_response = {
            "searchParameters": {
                "q": query,
                "gl": "us",
                "hl": "en",
                "num": num_results
            },
            "organic": []
        }
        
        # Create mock organic results based on the query
        for i in range(min(num_results, 5)):  # Limit to 5 results for simplicity
            mock_result = {
                "title": f"Mock Result {i+1} for {query}",
                "link": f"https://example.com/result-{i+1}",
                "snippet": f"This is a mock search result {i+1} for query: {query}. Created for testing purposes when no API key is available.",
                "position": i+1,
                "source": "example.com",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            mock_response["organic"].append(mock_result)
            
        # Add a mock knowledge graph for certain queries
        if "fact check" in query.lower():
            mock_response["knowledgeGraph"] = {
                "title": f"Fact Check: {query.replace('fact check', '').strip()}",
                "type": "Fact Check Result",
                "description": "This is a mock fact check result generated for testing purposes. In a real search, this would contain relevant fact-checking information.",
                "attributes": {
                    "Source": "Mock Fact Checker",
                    "Rating": "Unverified - Mock Data",
                    "Date": datetime.now().strftime("%Y-%m-%d")
                }
            }
            
        return mock_response
        
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
        
        # Add a note if using mock mode
        if self.mock_mode:
            results["mock_mode"] = True
        
        # Format results for fact checking
        formatted_results = {
            "claim": claim,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "fact_check_results": results,
            "information_results": {}  # Will be filled with additional info in a real scenario
        }
        
        # Add a second search for just information (not fact checking)
        try:
            info_query = claim
            info_results = await self.search(info_query)
            formatted_results["information_results"] = info_results
        except Exception as e:
            logger.warning(f"Information search failed, continuing with fact check only: {str(e)}")
        
        return formatted_results
        
# Helper function to create a new instance with default settings
def create_search_client(api_key: Optional[str] = None, mock_mode: bool = False) -> SearchAPIClient:
    """Create a new search client instance with default settings.
    
    Args:
        api_key: Optional API key (will use env variable if not provided)
        mock_mode: If True, will use mock responses when no API key is available
        
    Returns:
        Configured SearchAPIClient instance
    """
    return SearchAPIClient(api_key, mock_mode) 
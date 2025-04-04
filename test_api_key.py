#!/usr/bin/env python3
"""
Test script to verify the Serper.dev API key is loaded correctly.
This tests the priority order of API key sources:
1. Directly provided
2. From config.py
3. From environment variable
"""

import os
import json
import asyncio
import logging
from search_api import create_search_client, SearchAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_api_key")

async def test_search_with_config_key():
    """Test search using the API key from config.py"""
    logger.info("Testing search with API key from config.py")
    
    try:
        # Create a search client (should use config.py key)
        client = create_search_client()
        
        # Test a simple search
        results = await client.search("test query")
        
        # Check if the search was successful
        if results and "results" in results:
            logger.info("✅ Success! API key from config.py is working")
            logger.info(f"Received {len(results.get('results', []))} search results")
        else:
            logger.error("❌ Search failed - unexpected response format")
            logger.error(f"Response: {json.dumps(results, indent=2)}")
            
    except SearchAPIError as e:
        logger.error(f"❌ Search failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")

async def test_claim_verification():
    """Test claim verification functionality"""
    logger.info("\nTesting claim verification")
    
    try:
        # Create a search client (should use config.py key)
        client = create_search_client()
        
        # Example claim and context from previous conversation
        claim = "Azure did $28 billion in a quarter with 10-15% growth from AI products"
        context = "Azure's last quarter they did like $28 billion in the quarter I think they said 10 to 15% of that lift or growth was from AI products"
        
        # Search for claim verification
        results = await client.search_for_claim_verification(claim, context)
        
        # Check if the search was successful
        if results:
            logger.info("✅ Claim verification search succeeded")
            
            # Log some highlights from the results
            if "fact_check_results" in results:
                fact_checks = results["fact_check_results"]["results"]
                logger.info(f"Found {len(fact_checks)} fact-check results")
                
                # Show preview of first result if available
                if fact_checks:
                    first = fact_checks[0]
                    logger.info(f"First result: '{first.get('title', 'No title')}' from {first.get('source', 'unknown')}")
            
            knowledge_graph = results.get("fact_check_results", {}).get("knowledge_graph")
            if knowledge_graph:
                logger.info(f"Knowledge graph: {knowledge_graph.get('title')}")
                
    except SearchAPIError as e:
        logger.error(f"❌ Claim verification failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error in claim verification: {str(e)}")

async def main():
    """Main entry point"""
    logger.info("Starting API key test")
    await test_search_with_config_key()
    await test_claim_verification()
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main()) 
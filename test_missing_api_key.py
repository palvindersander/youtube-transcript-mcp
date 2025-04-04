#!/usr/bin/env python3
"""
Test script to verify error handling when Search API key is missing.
This test reproduces the error from Claude conversation where
search_for_claim_verification fails with "No Search API key configured" error.

Usage: python3 test_missing_api_key.py
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional

import search_api
from search_api import SearchAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_missing_api_key")

async def test_missing_api_key():
    """
    Test that reproduces the Claude conversation error where search_for_claim_verification
    fails because no Search API key is configured.
    """
    # First, save any existing API key so we can restore it later
    original_api_key = os.environ.get("SEARCH_API_KEY")
    
    # Remove the API key from environment to simulate the missing key scenario
    if "SEARCH_API_KEY" in os.environ:
        del os.environ["SEARCH_API_KEY"]
    
    logger.info("Testing search without API key (expecting error)")
    
    # Test data from Claude conversation
    claim = "Azure did $28 billion in a quarter with 10-15% growth from AI products"
    context = "Azure's last quarter they did like $28 billion in the quarter I think they said 10 to 15% of that lift or growth was from AI products"
    
    # Create client and try to search - this should fail
    client = search_api.create_search_client()
    
    try:
        # This should raise SearchAPIError because no API key is configured
        await client.search_for_claim_verification(claim, context)
        # If we get here, something is wrong - the call should have failed
        logger.error("ERROR: Search succeeded despite missing API key!")
        
    except SearchAPIError as e:
        # This is the expected error
        logger.info(f"Successfully caught expected error: {str(e)}")
        if "No Search API key configured" in str(e):
            logger.info("PASS: Correct error message detected")
        else:
            logger.error(f"ERROR: Unexpected error message: {str(e)}")
            
    except Exception as e:
        # This is an unexpected error
        logger.error(f"ERROR: Unexpected exception type: {type(e).__name__}")
        logger.error(f"ERROR: Exception message: {str(e)}")
    
    finally:
        # Restore original API key if it existed
        if original_api_key:
            os.environ["SEARCH_API_KEY"] = original_api_key
        
    # Now test what happens in the MCP server
    logger.info("\nTesting what would happen in the MCP server:")
    
    # Create a mock MCP search function to simulate what happens in transcript_mcp.py
    async def mock_mcp_search_for_claim_verification(claim: str, context: Optional[str] = None) -> str:
        """Simulate the MCP server's search_for_claim_verification tool behavior"""
        try:
            client = search_api.create_search_client()
            results = await client.search_for_claim_verification(claim, context)
            # Format as JSON string for Claude to parse
            return json.dumps(results, indent=2)
        except SearchAPIError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    # Test the mock MCP function
    result = await mock_mcp_search_for_claim_verification(claim, context)
    logger.info(f"MCP result: {result}")
    
    # Verify the result
    if "Error: No Search API key configured" in result:
        logger.info("PASS: MCP correctly handled the missing API key")
    else:
        logger.error(f"ERROR: MCP didn't handle missing API key correctly")

async def main():
    """Main entry point"""
    logger.info("Starting missing API key test")
    await test_missing_api_key()
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main()) 
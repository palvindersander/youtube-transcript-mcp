#!/usr/bin/env python3
"""
Test script to verify error handling when Search API key is missing.
This test reproduces the error from Claude conversation where
search_for_claim_verification fails with "No Search API key configured" error.

It also tests the new mock mode functionality that enables searches to go through
even when no API key is available.

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
    
    # Test data from Claude conversation
    claim = "Azure did $28 billion in a quarter with 10-15% growth from AI products"
    context = "Azure's last quarter they did like $28 billion in the quarter I think they said 10 to 15% of that lift or growth was from AI products"
    
    try:
        logger.info("\n=== Part 1: Testing search without API key and without mock mode ===")
        # Create client and try to search - this should fail without mock mode
        client = search_api.create_search_client(mock_mode=False)
        
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
        
        logger.info("\n=== Part 2: Testing search with mock mode enabled ===")
        # Create a new client with mock mode enabled - this should work even without an API key
        mock_client = search_api.create_search_client(mock_mode=True)
        
        try:
            # This should succeed using mock responses
            results = await mock_client.search_for_claim_verification(claim, context)
            
            # Check if we got mock results
            if results.get("mock_mode", False):
                logger.info("PASS: Search succeeded with mock mode")
                
                # Verify the structure of mock results
                if "fact_check_results" in results and "information_results" in results:
                    logger.info("PASS: Mock results have the expected structure")
                    
                    # Log a sample of the results
                    fact_check_count = len(results.get("fact_check_results", {}).get("results", []))
                    info_count = len(results.get("information_results", {}).get("results", []))
                    logger.info(f"Mock results returned {fact_check_count} fact-check results and {info_count} information results")
                    
                    if fact_check_count > 0:
                        first_result = results["fact_check_results"]["results"][0]
                        logger.info(f"Sample mock result: {first_result.get('title')}")
                else:
                    logger.error("ERROR: Mock results missing expected structure")
            else:
                logger.error("ERROR: Mock mode flag not set in results")
        
        except Exception as e:
            # This is unexpected - mock mode should not throw exceptions
            logger.error(f"ERROR: Mock mode search failed: {str(e)}")
            
        # Now test what happens in the MCP server
        logger.info("\n=== Part 3: Testing what would happen in the MCP server ===")
        
        # Create mock MCP search functions to simulate both behaviors in transcript_mcp.py
        async def mock_mcp_without_mock_mode(claim: str, context: Optional[str] = None) -> str:
            """Simulate the MCP server's search_for_claim_verification tool behavior without mock mode"""
            try:
                client = search_api.create_search_client(mock_mode=False)
                results = await client.search_for_claim_verification(claim, context)
                # Format as JSON string for Claude to parse
                return json.dumps(results, indent=2)
            except SearchAPIError as e:
                return f"Error: {str(e)}"
            except Exception as e:
                return f"Unexpected error: {str(e)}"
        
        async def mock_mcp_with_mock_mode(claim: str, context: Optional[str] = None) -> str:
            """Simulate the MCP server's search_for_claim_verification tool behavior with mock mode"""
            try:
                client = search_api.create_search_client(mock_mode=True)
                results = await client.search_for_claim_verification(claim, context)
                
                # Add a note if using mock mode
                if results.get("mock_mode", False):
                    mock_notice = "\n[NOTE: Using mock search results for demonstration purposes. To use real search results, set the SEARCH_API_KEY environment variable.]\n"
                    # Format as JSON string for Claude to parse
                    json_results = json.dumps(results, indent=2)
                    return mock_notice + json_results
                
                # Format as JSON string for Claude to parse
                return json.dumps(results, indent=2)
            except SearchAPIError as e:
                return f"Error: {str(e)}"
            except Exception as e:
                return f"Unexpected error: {str(e)}"
        
        # Test the mock MCP function without mock mode
        result_without_mock = await mock_mcp_without_mock_mode(claim, context)
        logger.info(f"MCP result without mock mode: {result_without_mock}")
        
        # Verify the result
        if "Error: No Search API key configured" in result_without_mock:
            logger.info("PASS: MCP without mock mode correctly handled the missing API key")
        else:
            logger.error(f"ERROR: MCP without mock mode didn't handle missing API key correctly")
        
        # Test the mock MCP function with mock mode
        result_with_mock = await mock_mcp_with_mock_mode(claim, context)
        logger.info(f"MCP result with mock mode: {result_with_mock[:200]}...")  # Only show the beginning
        
        # Verify the result
        if "[NOTE: Using mock search results" in result_with_mock:
            logger.info("PASS: MCP with mock mode correctly returns mock search results")
        else:
            logger.error(f"ERROR: MCP with mock mode didn't return mock search results correctly")
    
    finally:
        # Restore original API key if it existed
        if original_api_key:
            os.environ["SEARCH_API_KEY"] = original_api_key

async def main():
    """Main entry point"""
    logger.info("Starting missing API key test")
    await test_missing_api_key()
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main()) 
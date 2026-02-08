from typing import List, Dict, Any
from fastmcp import FastMCP
from supabase import create_client

mcp = FastMCP("Enrichment MCP Server")


@mcp.tool
def search_tickets_by_user(
    username: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains a user with the specified username in the users array.
    
    """
    try:
        SUPABASE_URL = "https://crxfcvskhqhxgjinofkh.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNyeGZjdnNraHFoeGdqaW5vZmtoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODUzMzc0MywiZXhwIjoyMDY0MTA5NzQzfQ.y3SLvvzfwUoUmyfova_tCA6xvL2C9qKWcvaDEuqMYX0"
        
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as client_init_error:
            error_msg = str(client_init_error)
            if "Name or service not known" in error_msg or "Errno -2" in error_msg or "Failed to resolve" in error_msg:
                return [{"error": f"Client initialization - Network/DNS error: Cannot connect to Supabase. Please check your internet connection and verify the Supabase URL is correct: {SUPABASE_URL}. Error: {error_msg}"}]
            return [{"error": f"Client initialization failed: {error_msg}"}]
        
        # Try to use database-level JSONB filtering for better performance
        # This uses PostgREST's JSONB contains operator to filter at the database level
        try:
            # Use JSONB path query: check if artifacts_and_assets->users contains an object with matching value
            # The 'cs' operator checks if the left JSONB value contains the right JSONB value
            response = supabase.table("tickets").select("*").filter(
                "artifacts_and_assets->users",
                "cs",
                f'[{{"value":"{username}"}}]'
            ).execute()
            
            if response.data:
                return response.data
        except Exception as jsonb_filter_error:
            # If JSONB filter fails, fall back to client-side filtering
            # This can happen if the filter syntax isn't supported or there's a schema issue
            error_msg = str(jsonb_filter_error)
            # Check if it's a network error - if so, return early
            if "Name or service not known" in error_msg or "Errno -2" in error_msg or "Failed to resolve" in error_msg:
                return [{"error": f"JSONB filter query - Network/DNS error: Cannot connect to Supabase. Please check your internet connection and verify the Supabase URL is correct: {SUPABASE_URL}. Error: {error_msg}"}]
            # Otherwise, continue with fallback
            print(f"JSONB filter failed, using fallback: {jsonb_filter_error}")
        
        # Fallback: Fetch all tickets and filter in Python
        # This is less efficient but works reliably
        try:
            response = supabase.table("tickets").select("*").execute()
        except Exception as fallback_query_error:
            error_msg = str(fallback_query_error)
            if "Name or service not known" in error_msg or "Errno -2" in error_msg or "Failed to resolve" in error_msg:
                return [{"error": f"Fallback query - Network/DNS error: Cannot connect to Supabase. Please check your internet connection and verify the Supabase URL is correct: {SUPABASE_URL}. Error: {error_msg}"}]
            else:
                return [{"error": f"Fallback query failed: {error_msg}"}]
        
        if not response.data:
            return []
        
        # Filter tickets where artifacts_and_assets.users contains a user with matching value
        matching_tickets = []
        for ticket in response.data:
            artifacts = ticket.get("artifacts_and_assets")
            
            # Skip if artifacts_and_assets is None or not a dict
            if not isinstance(artifacts, dict):
                continue
                
            users = artifacts.get("users", [])
            
            # Skip if users is not a list
            if not isinstance(users, list):
                continue
            
            # Check if any user in the array has a matching value
            for user in users:
                if isinstance(user, dict) and user.get("value") == username:
                    matching_tickets.append(ticket)
                    break  # Found a match, no need to check other users in this ticket
        
        return matching_tickets
        
    except Exception as general_error:
        error_msg = str(general_error)
        if "Name or service not known" in error_msg or "Errno -2" in error_msg or "Failed to resolve" in error_msg:
            return [{"error": f"General error - Network/DNS error: Cannot connect to Supabase. Please check your internet connection and verify the Supabase URL is correct: {SUPABASE_URL}. Error: {error_msg}"}]
        return [{"error": f"General unexpected error: {error_msg}"}]


@mcp.tool
def add(
    sessionId: str,
    action: str,
    chatInput: str,
    toolCallId: str,
    a: int,
    b: int,
) -> int:
    # Ignore context fields, use only what is required
    return a + b


if __name__ == "__main__":
    mcp.run()

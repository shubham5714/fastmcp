from typing import List, Dict, Any
from fastmcp import FastMCP
from supabase import create_client, Client

mcp = FastMCP("Enrichment MCP Server")

# Supabase configuration - replace with your actual credentials
SUPABASE_URL = "https://crxfcvskhqhxgjinofkh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNyeGZjdnNraHFoeGdqaW5vZmtoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODUzMzc0MywiZXhwIjoyMDY0MTA5NzQzfQ.y3SLvvzfwUoUmyfova_tCA6xvL2C9qKWcvaDEuqMYX0"

# Initialize Supabase client
def get_supabase_client() -> Client:
    """Initialize and return Supabase client using hardcoded credentials."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@mcp.tool
def search_tickets_by_user(
    username: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains a user with the specified username in the users array.
    
    The artifacts_and_assets column contains JSON with a "users" array where each user
    object has a "value" field. This function searches for tickets where any user's
    value matches the provided username.
    
    Args:
        username: The username to search for in the artifacts_and_assets.users array
        
    Returns:
        List of tickets matching the username, or list with error dict if query fails
    """
    try:
        supabase = get_supabase_client()
        
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
        except Exception as filter_error:
            # If JSONB filter fails, fall back to client-side filtering
            # This can happen if the filter syntax isn't supported or there's a schema issue
            error_msg = str(filter_error)
            # Check if it's a network error - if so, return early
            if "Name or service not known" in error_msg or "Errno -2" in error_msg or "Failed to resolve" in error_msg:
                return [{"error": f"Network/DNS error: Cannot connect to Supabase. Please check your internet connection and verify the Supabase URL is correct: {SUPABASE_URL}. Error: {error_msg}"}]
            # Otherwise, continue with fallback
            print(f"JSONB filter failed, using fallback: {filter_error}")
        
        # Fallback: Fetch all tickets and filter in Python
        # This is less efficient but works reliably
        try:
            response = supabase.table("tickets").select("*").execute()
        except Exception as query_error:
            error_msg = str(query_error)
            if "Name or service not known" in error_msg or "Errno -2" in error_msg or "Failed to resolve" in error_msg:
                return [{"error": f"Network/DNS error: Cannot connect to Supabase. Please check your internet connection and verify the Supabase URL is correct: {SUPABASE_URL}. Error: {error_msg}"}]
            else:
                return [{"error": f"Supabase query failed: {error_msg}"}]
        
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
        
    except Exception as e:
        error_msg = str(e)
        if "Name or service not known" in error_msg or "Errno -2" in error_msg or "Failed to resolve" in error_msg:
            return [{"error": f"Network/DNS error: Cannot connect to Supabase. Please check your internet connection and verify the Supabase URL is correct: {SUPABASE_URL}. Error: {error_msg}"}]
        return [{"error": f"Unexpected error: {error_msg}"}]


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

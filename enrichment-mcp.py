from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastmcp import FastMCP
from supabase import create_client

mcp = FastMCP("Enrichment MCP Server")


def extract_ticket_fields(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract only id and name from tickets."""
    return [
        {
            "id": ticket.get("id", ""),
            "name": ticket.get("name", "")
        }
        for ticket in tickets
    ]


@mcp.tool
def search_tickets_by_user(
    username: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains a user with the specified username in the users array.
    
    """
    print(f"Searching for tickets by user: {username}")
    try:
        SUPABASE_URL = "https://zhhsijigoupqroztdrdy.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpoaHNpamlnb3VwcXJvenRkcmR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwNjgyODksImV4cCI6MjA3MjY0NDI4OX0.Mxq7DYbKV9OXHS7eE1YpdQ4F8Htld0Vt6FwlfOpX8kQ"
       
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as client_init_error:
            error_msg = str(client_init_error)
            return [{"error": f"Client initialization failed: {error_msg}"}]
        
        # Use database-level JSONB filtering
        # This uses PostgREST's JSONB contains operator to filter at the database level
        # Filter for tickets from the last 7 days
        try:
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            response = supabase.table("tickets").select("*").filter(
                "artifacts_and_assets->users",
                "cs",
                f'[{{"value":"{username}"}}]'
            ).gte("created_at", seven_days_ago).execute()
            
            if response.data:
                tickets = extract_ticket_fields(response.data)
                data = {"users": tickets}
                total_count = len(tickets)
                return [{"total_count": total_count, "data": data}]
            data = {"users": []}
            return [{"total_count": 0, "data": data}]
        except Exception as jsonb_filter_error:
            error_msg = str(jsonb_filter_error)
            return [{"error": f"JSONB filter query failed: {error_msg}"}]
        
    except Exception as general_error:
        error_msg = str(general_error)
        return [{"error": f"General error: {error_msg}"}]


@mcp.tool
def search_tickets_by_asset(
    asset: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains an asset with the specified asset name in the assets array.
    
    """
    print(f"Searching for tickets by asset: {asset}")
    try:
        SUPABASE_URL = "https://zhhsijigoupqroztdrdy.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpoaHNpamlnb3VwcXJvenRkcmR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwNjgyODksImV4cCI6MjA3MjY0NDI4OX0.Mxq7DYbKV9OXHS7eE1YpdQ4F8Htld0Vt6FwlfOpX8kQ"
       
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as client_init_error:
            error_msg = str(client_init_error)
            return [{"error": f"Client initialization failed: {error_msg}"}]
        
        # Use database-level JSONB filtering
        # This uses PostgREST's JSONB contains operator to filter at the database level
        # Filter for tickets from the last 7 days
        try:
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            response = supabase.table("tickets").select("*").filter(
                "artifacts_and_assets->assets",
                "cs",
                f'[{{"value":"{asset}"}}]'
            ).gte("created_at", seven_days_ago).execute()
            
            if response.data:
                tickets = extract_ticket_fields(response.data)
                data = {"assets": tickets}
                total_count = len(tickets)
                return [{"total_count": total_count, "data": data}]
            data = {"assets": []}
            return [{"total_count": 0, "data": data}]
        except Exception as jsonb_filter_error:
            error_msg = str(jsonb_filter_error)
            return [{"error": f"JSONB filter query failed: {error_msg}"}]
        
    except Exception as general_error:
        error_msg = str(general_error)
        return [{"error": f"General error: {error_msg}"}]


if __name__ == "__main__":
    mcp.run()

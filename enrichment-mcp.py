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
        try:
            response = supabase.table("tickets").select("*").filter(
                "artifacts_and_assets->users",
                "cs",
                f'[{{"value":"{username}"}}]'
            ).execute()
            
            if response.data:
                return response.data
            return []
        except Exception as jsonb_filter_error:
            error_msg = str(jsonb_filter_error)
            return [{"error": f"JSONB filter query failed: {error_msg}"}]
        
    except Exception as general_error:
        error_msg = str(general_error)
        return [{"error": f"General error: {error_msg}"}]


if __name__ == "__main__":
    mcp.run()

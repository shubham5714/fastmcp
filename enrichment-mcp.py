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
    id: str,
    username: str,
) -> List[Dict[str, Any]]:
    """
    This tool Search for Related Alerts in database for Given Username.
    
    """
    print(f"Searching for tickets by user: {username}, updating ticket id: {id}")
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
                
                # Update related_alerts column only for the ticket with the provided id
                default_related_alerts = {
                    "users": {},
                    "assets": {},
                    "ips": {},
                    "domains": {},
                    "hashes": {},
                    "urls": {}
                }
                
                # Get current related_alerts from database to preserve existing data
                try:
                    ticket_response = supabase.table("tickets").select("related_alerts").eq("id", id).execute()
                    if ticket_response.data and ticket_response.data[0].get("related_alerts"):
                        current_related_alerts = ticket_response.data[0]["related_alerts"]
                        # Ensure it's a dict and has all required keys
                        if not isinstance(current_related_alerts, dict):
                            current_related_alerts = default_related_alerts.copy()
                    else:
                        current_related_alerts = default_related_alerts.copy()
                except Exception:
                    # If fetch fails, use default structure
                    current_related_alerts = default_related_alerts.copy()
                
                # Ensure all keys exist (preserve existing data in each key)
                for key in default_related_alerts.keys():
                    if key not in current_related_alerts:
                        current_related_alerts[key] = {}
                    elif not isinstance(current_related_alerts[key], dict):
                        current_related_alerts[key] = {}
                
                # Update only the specific username entry, preserving other users
                current_related_alerts["users"][username] = tickets
                
                # Update only the ticket with the provided id
                try:
                    supabase.table("tickets").update({
                        "related_alerts": current_related_alerts
                    }).eq("id", id).execute()
                except Exception as update_error:
                    print(f"Failed to update ticket {id}: {update_error}")
                
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
    id: str,
    asset: str,
) -> List[Dict[str, Any]]:
    """
    This tool Search for Related Alerts in database for Given Asset name.
    
    """
    print(f"Searching for tickets by asset: {asset}, updating ticket id: {id}")
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
                
                # Update related_alerts column only for the ticket with the provided id
                default_related_alerts = {
                    "users": {},
                    "assets": {},
                    "ips": {},
                    "domains": {},
                    "hashes": {},
                    "urls": {}
                }
                
                # Get current related_alerts from database to preserve existing data
                try:
                    ticket_response = supabase.table("tickets").select("related_alerts").eq("id", id).execute()
                    if ticket_response.data and ticket_response.data[0].get("related_alerts"):
                        current_related_alerts = ticket_response.data[0]["related_alerts"]
                        # Ensure it's a dict and has all required keys
                        if not isinstance(current_related_alerts, dict):
                            current_related_alerts = default_related_alerts.copy()
                    else:
                        current_related_alerts = default_related_alerts.copy()
                except Exception:
                    # If fetch fails, use default structure
                    current_related_alerts = default_related_alerts.copy()
                
                # Ensure all keys exist (preserve existing data in each key)
                for key in default_related_alerts.keys():
                    if key not in current_related_alerts:
                        current_related_alerts[key] = {}
                    elif not isinstance(current_related_alerts[key], dict):
                        current_related_alerts[key] = {}
                
                # Update only the specific asset entry, preserving other assets
                current_related_alerts["assets"][asset] = tickets
                
                # Update only the ticket with the provided id
                try:
                    supabase.table("tickets").update({
                        "related_alerts": current_related_alerts
                    }).eq("id", id).execute()
                except Exception as update_error:
                    print(f"Failed to update ticket {id}: {update_error}")
                
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

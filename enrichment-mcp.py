from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastmcp import FastMCP
from supabase import create_client

mcp = FastMCP("Enrichment MCP Server")

def extract_ticket_fields(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract id, time, name, severity, status, and closure_category from tickets."""
    return [
        {
            "id": ticket.get("id", ""),
            "time": ticket.get("occurred_at", ""),
            "name": ticket.get("name", ""),
            "severity": ticket.get("severity", ""),
            "status": ticket.get("status", ""),
            "closure_category": ticket.get("closure_category", "")
        }
        for ticket in tickets
    ]


@mcp.tool
def search_tickets_by_user(
    id: int,
    username: str,
    tenant_id: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains a user with the specified username in the users array.
    Updates related_alerts only for the ticket with the provided id.
    
    """
    print(f"Searching for tickets by user: {username}, tenant_id: {tenant_id}, updating ticket id: {id}")
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
            ).eq("tenant_id", tenant_id).gte("created_at", seven_days_ago).execute()
            
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
    id: int,
    asset: str,
    tenant_id: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains an asset with the specified asset name in the assets array.
    Updates related_alerts only for the ticket with the provided id.
    
    """
    print(f"Searching for tickets by asset: {asset}, tenant_id: {tenant_id}, updating ticket id: {id}")
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
            ).eq("tenant_id", tenant_id).gte("created_at", seven_days_ago).execute()
            
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


@mcp.tool
def search_tickets_by_ip(
    id: int,
    ip: str,
    tenant_id: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains an IP address with the specified IP in the artifacts->ip_addresses array.
    Updates related_alerts only for the ticket with the provided id.
    
    """
    print(f"Searching for tickets by IP: {ip}, tenant_id: {tenant_id}, updating ticket id: {id}")
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
                "artifacts_and_assets->artifacts->ip_addresses",
                "cs",
                f'[{{"value":"{ip}"}}]'
            ).eq("tenant_id", tenant_id).gte("created_at", seven_days_ago).execute()
            
            if response.data:
                tickets = extract_ticket_fields(response.data)
                data = {"ips": tickets}
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
                
                # Update only the specific IP entry, preserving other IPs
                current_related_alerts["ips"][ip] = tickets
                
                # Update only the ticket with the provided id
                try:
                    supabase.table("tickets").update({
                        "related_alerts": current_related_alerts
                    }).eq("id", id).execute()
                except Exception as update_error:
                    print(f"Failed to update ticket {id}: {update_error}")
                
                return [{"total_count": total_count, "data": data}]
            data = {"ips": []}
            return [{"total_count": 0, "data": data}]
        except Exception as jsonb_filter_error:
            error_msg = str(jsonb_filter_error)
            return [{"error": f"JSONB filter query failed: {error_msg}"}]
        
    except Exception as general_error:
        error_msg = str(general_error)
        return [{"error": f"General error: {error_msg}"}]


@mcp.tool
def search_tickets_by_domain(
    id: int,
    domain: str,
    tenant_id: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains a domain with the specified domain in the artifacts->domains array.
    Updates related_alerts only for the ticket with the provided id.
    
    """
    print(f"Searching for tickets by domain: {domain}, tenant_id: {tenant_id}, updating ticket id: {id}")
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
                "artifacts_and_assets->artifacts->domains",
                "cs",
                f'[{{"value":"{domain}"}}]'
            ).eq("tenant_id", tenant_id).gte("created_at", seven_days_ago).execute()
            
            if response.data:
                tickets = extract_ticket_fields(response.data)
                data = {"domains": tickets}
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
                
                # Update only the specific domain entry, preserving other domains
                current_related_alerts["domains"][domain] = tickets
                
                # Update only the ticket with the provided id
                try:
                    supabase.table("tickets").update({
                        "related_alerts": current_related_alerts
                    }).eq("id", id).execute()
                except Exception as update_error:
                    print(f"Failed to update ticket {id}: {update_error}")
                
                return [{"total_count": total_count, "data": data}]
            data = {"domains": []}
            return [{"total_count": 0, "data": data}]
        except Exception as jsonb_filter_error:
            error_msg = str(jsonb_filter_error)
            return [{"error": f"JSONB filter query failed: {error_msg}"}]
        
    except Exception as general_error:
        error_msg = str(general_error)
        return [{"error": f"General error: {error_msg}"}]


@mcp.tool
def search_tickets_by_hash(
    id: int,
    hash_value: str,
    tenant_id: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains a hash with the specified hash value in the artifacts->hashes array.
    Updates related_alerts only for the ticket with the provided id.
    
    """
    print(f"Searching for tickets by hash: {hash_value}, tenant_id: {tenant_id}, updating ticket id: {id}")
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
                "artifacts_and_assets->artifacts->hashes",
                "cs",
                f'[{{"value":"{hash_value}"}}]'
            ).eq("tenant_id", tenant_id).gte("created_at", seven_days_ago).execute()
            
            if response.data:
                tickets = extract_ticket_fields(response.data)
                data = {"hashes": tickets}
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
                
                # Update only the specific hash entry, preserving other hashes
                current_related_alerts["hashes"][hash_value] = tickets
                
                # Update only the ticket with the provided id
                try:
                    supabase.table("tickets").update({
                        "related_alerts": current_related_alerts
                    }).eq("id", id).execute()
                except Exception as update_error:
                    print(f"Failed to update ticket {id}: {update_error}")
                
                return [{"total_count": total_count, "data": data}]
            data = {"hashes": []}
            return [{"total_count": 0, "data": data}]
        except Exception as jsonb_filter_error:
            error_msg = str(jsonb_filter_error)
            return [{"error": f"JSONB filter query failed: {error_msg}"}]
        
    except Exception as general_error:
        error_msg = str(general_error)
        return [{"error": f"General error: {error_msg}"}]


@mcp.tool
def search_tickets_by_url(
    id: int,
    url: str,
    tenant_id: str,
) -> List[Dict[str, Any]]:
    """
    Search for tickets in the tickets table where the artifacts_and_assets JSONB column
    contains a URL with the specified url in the artifacts->urls array.
    Updates related_alerts only for the ticket with the provided id.
    
    """
    print(f"Searching for tickets by URL: {url}, tenant_id: {tenant_id}, updating ticket id: {id}")
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
                "artifacts_and_assets->artifacts->urls",
                "cs",
                f'[{{"value":"{url}"}}]'
            ).eq("tenant_id", tenant_id).gte("created_at", seven_days_ago).execute()
            
            if response.data:
                tickets = extract_ticket_fields(response.data)
                data = {"urls": tickets}
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
                
                # Update only the specific URL entry, preserving other URLs
                current_related_alerts["urls"][url] = tickets
                
                # Update only the ticket with the provided id
                try:
                    supabase.table("tickets").update({
                        "related_alerts": current_related_alerts
                    }).eq("id", id).execute()
                except Exception as update_error:
                    print(f"Failed to update ticket {id}: {update_error}")
                
                return [{"total_count": total_count, "data": data}]
            data = {"urls": []}
            return [{"total_count": 0, "data": data}]
        except Exception as jsonb_filter_error:
            error_msg = str(jsonb_filter_error)
            return [{"error": f"JSONB filter query failed: {error_msg}"}]
        
    except Exception as general_error:
        error_msg = str(general_error)
        return [{"error": f"General error: {error_msg}"}]


if __name__ == "__main__":
    mcp.run()

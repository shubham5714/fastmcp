import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastmcp import FastMCP
from prefect.deployments import run_deployment
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
    id: str,
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
    id: str,
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
    id: str,
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
    id: str,
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
    id: str,
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
def get_mitre_by_name(
    name: str,
    tenant_id: str,
) -> List[Dict[str, Any]]:
    """
    Get the mitre JSON column from the tickets table by ticket name and tenant_id.
    Returns an empty list if no rows are found.
    """
    print(f"Getting mitre by name: {name}, tenant_id: {tenant_id}")
    try:
        SUPABASE_URL = "https://zhhsijigoupqroztdrdy.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpoaHNpamlnb3VwcXJvenRkcmR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwNjgyODksImV4cCI6MjA3MjY0NDI4OX0.Mxq7DYbKV9OXHS7eE1YpdQ4F8Htld0Vt6FwlfOpX8kQ"

        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as client_init_error:
            error_msg = str(client_init_error)
            return [{"error": f"Client initialization failed: {error_msg}"}]

        try:
            response = (
                supabase.table("tickets")
                .select("mitre")
                .eq("name", name)
                .eq("tenant_id", tenant_id)
                .limit(1)
                .execute()
            )

            if not response.data:
                return []

            mitre_data = response.data[0].get("mitre")
            if mitre_data is None:
                return []

            if isinstance(mitre_data, dict):
                return [mitre_data]
            return [{"mitre": mitre_data}]
        except Exception as query_error:
            error_msg = str(query_error)
            return [{"error": f"Query failed: {error_msg}"}]
    except Exception as general_error:
        error_msg = str(general_error)
        return [{"error": f"General error: {error_msg}"}]


@mcp.tool
def search_tickets_by_url(
    id: str,
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


GURUCUL_COMMAND = "gra-search"
GURUCUL_DEFAULT_PAGE = 1
GURUCUL_DEFAULT_MAX = 100
GURUCUL_DEPLOYMENT_TIMEOUT = 600
GURUCUL_POLL_INTERVAL = 5


@mcp.tool
def gurucul_search_tool(
    query: str,
    instance_name: str,
    instance_id: int,
    from_date: str,
    to_date: str,
) -> List[Dict[str, Any]]:
    """
    This tool searches Gurucul GRA logs within the specified time range and supports filtering, aggregation, and grouping.

    Args:
        query: Gurucul GRA search query, for example
         1.  group by datasourcename  #explore the datasources available
         2.  datasourcename = "Fortinet" group by logtype #pivot to specific datasource and explore the categories available
         3.  ((datasourcename = "Fortinet"  and logtype = "utm"  )) and application = "Google.Drive" #filter to specific categories
        instance_name: Gurucul instance name, for example "Gurucul SIEM".
        instance_id: Gurucul instance id passed to the deployment as integration_id, for example 62
        from_date: Start of the search window in UTC, format YYYY-MM-DD HH:MM:SS
        to_date: End of the search window in UTC, format YYYY-MM-DD HH:MM:SS
    """
    prefect_api_url = os.getenv("PREFECT_API_URL")
    if not prefect_api_url:
        return [{"state": "FAILED", "result": "PREFECT_API_URL is not set in the MCP server environment"}]

    os.environ["PREFECT_API_URL"] = prefect_api_url
    prefect_auth_string = os.getenv("PREFECT_API_AUTH_STRING")
    if prefect_auth_string:
        os.environ["PREFECT_API_AUTH_STRING"] = prefect_auth_string

    try:
        flow_run = run_deployment(
            name=f"{instance_name}/{instance_name}",
            parameters={
                "integration_id": instance_id,
                "command": GURUCUL_COMMAND,
                "argue": {
                    "query": query,
                    "fromDate": from_date,
                    "toDate": to_date,
                    "page": GURUCUL_DEFAULT_PAGE,
                    "max": GURUCUL_DEFAULT_MAX,
                },
            },
            timeout=GURUCUL_DEPLOYMENT_TIMEOUT,
            poll_interval=GURUCUL_POLL_INTERVAL,
        )

        state = str(flow_run.state.type) if flow_run.state else "FAILED"

        if not flow_run.state or not flow_run.state.is_final():
            return [{"state": state, "result": f"Deployment is still running after timeout: {flow_run.id}"}]

        if flow_run.state.is_failed():
            return [{"state": state, "result": flow_run.state.message}]

        try:
            from prefect_aws.s3 import S3Bucket  # noqa: F401
        except ImportError:
            return [{
                "state": state,
                "result": "Flow completed, but prefect-aws is not installed so the S3 result cannot be loaded. Add prefect-aws to the MCP server requirements.",
            }]

        try:
            return [{"state": state, "result": flow_run.state.result()}]
        except Exception as result_error:
            return [{"state": state, "result": str(result_error)}]
    except Exception as general_error:
        return [{"state": "FAILED", "result": str(general_error)}]


if __name__ == "__main__":
    mcp.run()

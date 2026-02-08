from typing import List, Optional, Any, Dict
import json

import ipinfo
from fastmcp import FastMCP
from pydantic import BaseModel
from supabase import create_client, Client


IPINFO_API_TOKEN = "5b3e1d46453882"
SUPABASE_URL = "https://crxfcvskhqhxgjinofkh.supabase.co"  # e.g., "https://your-project.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNyeGZjdnNraHFoeGdqaW5vZmtoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODUzMzc0MywiZXhwIjoyMDY0MTA5NzQzfQ.y3SLvvzfwUoUmyfova_tCA6xvL2C9qKWcvaDEuqMYX0"  # Your Supabase service key or anon key


class IPInfoResult(BaseModel):
    ip: str
    company: Optional[str] = None
    country_code: Optional[str] = None
    country: Optional[str] = None
    asn: Optional[str] = None
    as_name: Optional[str] = None


class TicketUserMatch(BaseModel):
    ticket_id: Any
    matched_user: str
    alerts: Optional[int] = None
    detail: Optional[str] = None
    raw_users: List[Dict[str, Any]]


class TicketUserSearchResult(BaseModel):
    username: str
    matches: List[TicketUserMatch]


mcp = FastMCP("enrichment-server")


def _get_supabase_client() -> Client:
    """
    Create and return a Supabase client using hardcoded credentials.
    """
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@mcp.tool()
def get_ipinfo(ip: str) -> IPInfoResult:
    """
    Look up company and country information for an IP address using the ipinfo.io SDK.

    Args:
        ip: IPv4 or IPv6 address to look up.

    Returns:
        IPInfoResult with company (from ASN name), country, and related fields.
    """
    handler = ipinfo.getHandlerLite(access_token=IPINFO_API_TOKEN)
    details = handler.getDetails(ip)

    ip_value = details.ip
    country_code = getattr(details, "country_code", None)
    country = getattr(details, "country", None)
    asn = getattr(details, "asn", None)
    as_name = getattr(details, "as_name", None)

    company = as_name

    return IPInfoResult(
        ip=ip_value,
        company=company,
        country_code=country_code,
        country=country,
        asn=asn,
        as_name=as_name,
    )


@mcp.tool()
def find_tickets_by_username(username: str) -> TicketUserSearchResult:
    """
    Search the Supabase `tickets` table for rows where the `artifacts_and_assets`
    JSON contains a user whose `value` matches the given username.

    The `artifacts_and_assets` column is expected to contain JSON like:
    {
      "users": [
        {"value": "john.doe@company.com", "alerts": 12, "detail": "Role: Administrator, Department: IT"},
        ...
      ],
      "assets": [...],
      "artifacts": {...}
    }

    This tool returns all tickets where any entry in `users` has a `value`
    that equals the provided `username` (case-insensitive string match).
    """
    supabase = _get_supabase_client()

    # Fetch all tickets. If you have a lot of rows, you may want to add filters
    # on Supabase side (e.g., using Postgres JSON operators) instead of scanning
    # client-side.
    response = supabase.table("tickets").select("*").execute()
    rows = response.data or []

    matches: List[TicketUserMatch] = []

    for row in rows:
        artifacts_raw = row.get("artifacts_and_assets")

        # Handle both text and JSON storage formats
        if isinstance(artifacts_raw, str):
            try:
                artifacts = json.loads(artifacts_raw)
            except json.JSONDecodeError:
                continue
        elif isinstance(artifacts_raw, dict):
            artifacts = artifacts_raw
        else:
            continue

        users = artifacts.get("users") or []
        if not isinstance(users, list):
            continue

        for user_entry in users:
            if not isinstance(user_entry, dict):
                continue

            value = user_entry.get("value")
            if value and value.lower() == username.lower():
                match = TicketUserMatch(
                    ticket_id=row.get("id"),
                    matched_user=value,
                    alerts=user_entry.get("alerts"),
                    detail=user_entry.get("detail"),
                    raw_users=users,
                )
                matches.append(match)

    return TicketUserSearchResult(username=username, matches=matches)


if __name__ == "__main__":
    mcp.run()


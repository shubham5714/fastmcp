from typing import Optional

import ipinfo
from fastmcp import FastMCP
from pydantic import BaseModel


IPINFO_API_TOKEN = "5b3e1d46453882"


class IPInfoResult(BaseModel):
    ip: str
    company: Optional[str] = None
    country_code: Optional[str] = None
    country: Optional[str] = None
    asn: Optional[str] = None
    as_name: Optional[str] = None


mcp = FastMCP("enrichment-server")


@mcp.tool()
def get_ipinfo(ip: str) -> IPInfoResult:
    """
    Look up company and country information for an IP address using the ipinfo.io SDK.

    Args:
        ip: IPv4 or IPv6 address to look up.

    Returns:
        IPInfoResult with company (from ASN name), country, and related fields.
    """
    # Use the Lite handler with the hardcoded token
    handler = ipinfo.getHandlerLite(access_token=IPINFO_API_TOKEN)
    details = handler.getDetails(ip)

    # Map fields similar to your example snippet
    ip_value = details.ip
    country_code = getattr(details, "country_code", None)
    country = getattr(details, "country", None)
    asn = getattr(details, "asn", None)
    as_name = getattr(details, "as_name", None)

    # Treat ASN name as the "company" for this tool's purpose
    company = as_name

    return IPInfoResult(
        ip=ip_value,
        company=company,
        country_code=country_code,
        country=country,
        asn=asn,
        as_name=as_name,
    )


if __name__ == "__main__":
    mcp.run()




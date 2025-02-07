import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import mcp.types as mcp_types
from mcp.server.fastmcp import FastMCP
from nostr_sdk import Client, EventBuilder, Keys, LogLevel, NostrSigner, init_logger
from pydantic import AnyUrl

from .util import async_http_get, async_http_post

# Initialize FastMCP server
mcp = FastMCP("goostr")

GOOSTR_NSEC = os.getenv("GOOSTR_NSEC")


@dataclass
class AgencyData:
    agency_id: Optional[int]
    toptier_code: Optional[str]
    abbreviation: Optional[str]
    agency_name: Optional[str]
    congressional_justification_url: Optional[str]

    @classmethod
    def from_api(cls, data: dict):
        return cls(
            agency_id=data.get("agency_id"),
            toptier_code=data.get("toptier_code"),
            abbreviation=data.get("abbreviation"),
            agency_name=data.get("agency_name"),
            congressional_justification_url=data.get("congressional_justification_url"),
        )


# @mcp.tool(name="PublishNote", description="Publish a Kind 1 Nostr note")
# async def publish_note(note: str) -> Dict[str, str]:
#     """Publish a Kind 1 nostr EventBuilder
#
#     Args:
#         note: Note content
#     """
#
#     init_logger(LogLevel.INFO)
#
#     keys = Keys.generate()
#     signer = NostrSigner.keys(keys)
#     client = Client(signer)
#
#     await client.add_relay("wss://relay.damus.io")
#     await client.add_relay("wss://nos.lol")
#
#     await client.connect()
#
#     builder = EventBuilder.text_note(note)
#     output = await client.send_event_builder(builder)
#
#     return {"npub": keys.public_key().to_bech32(), "note_id": output.id.to_bech32()}


@mcp.tool(
    name="GetGovSpendingAwards",
    description="Get government spending awards for a fiscal year for a given agency id",
)
async def get_gov_spending_by_fiscal_year(
    year: str, agency_id: str
) -> Dict[str, Any] | None:
    """Get government spending awards from usaspending.gov for a given agency id

    Args:
        year: fiscal year for which you want data
        toptier_agency: toptier agency code
    """
    URL = "https://api.usaspending.gov/api/v2/spending/"
    BODY = {
        "type": "award",
        "filters": {"fy": str(year), "period": "12", "agency": agency_id},
    }
    try:
        response = await async_http_post(URL, data=BODY)
        return response.json()
    except Exception as e:
        print(e)
        return None


@mcp.tool(
    name="GetAwardInfo", description="Get Details on a given Federal Spending award"
)
async def get_award_info(generated_unique_award_id: str) -> Dict[str, Any] | None:
    BASE_URL = "https://api.usaspending.gov/api/v2/awards/"
    URL = urljoin(BASE_URL, generated_unique_award_id)
    try:
        response = await async_http_get(URL)
        return response.json()
    except Exception as e:
        print(e)
        return None


@mcp.tool(
    name="GetAgencies",
    description="Get a list of all united states federal agencies and associated codes and IDs",
)
async def get_us_agencies() -> Dict[str, Any] | None:
    """Get US agencies and their ids and codes

    Usage:
        get_us_agencies()
    """
    URL = "https://api.usaspending.gov/api/v2/references/toptier_agencies/"
    try:
        response = await async_http_get(URL)
        return response.json()
        # return [AgencyData.from_api(i) for i in response.json().get("results")]
    except Exception as e:
        print(e)
        return None


# @mcp.list_resources()
# async def get_resources() -> List[mcp_types.Resource]:
#     return [
#         mcp_types.Resource(
#             uri= AnyUrl("agency://all"),
#             name="All United States Agencies",
#             description="Get a list of all United States federal agencies and their codes and IDs",
#             mimeType="text/plain",
#         )
#     ]

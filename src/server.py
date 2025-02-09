import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
import mcp.types as mcp_types
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from nostr_sdk import Client, EventBuilder, Keys, LogLevel, NostrSigner, init_logger
from pydantic import AnyUrl, BaseModel

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


class AwardsByAgencyAndFyArgs(BaseModel):
    year: str
    agency_id: str


@mcp.tool(name="GetSpendingAwardsByAgencyId")
async def get_gov_spending_by_fiscal_year(
    args: AwardsByAgencyAndFyArgs,
) -> Dict[str, Any]:
    """Get government spending awards from usaspending.gov for a fiscal year for a given agency id
    - Use this tool when you have an agency id and want to get awards for a given year
    Args:
        year: fiscal year for which you want data
        toptier_agency: toptier agency code
    """
    URL = "https://api.usaspending.gov/api/v2/spending/"
    BODY = {
        "type": "award",
        "filters": {"fy": args.year, "period": "12", "agency": args.agency_id},
    }
    try:
        response = await async_http_post(URL, json=BODY)
        return response.json()
    except httpx.HTTPStatusError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Received {e.response.status_code} from usaspending.gov while requesting {e.request.url}",
            )
        )
    except httpx.RequestError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Error while requesting {e.request.url}. Http Error: {e!r}",
            )
        )


class AwardDetailArgs(BaseModel):
    generated_unique_award_id: str


@mcp.tool(name="GetAwardInfoByAwardId")
async def get_award_info(args: AwardDetailArgs) -> Dict[str, Any] | None:
    """Get award details for a given award id from usaspending.gov
    - Use this when you have a generated award id from another tool and want to get details on that specific award
    - Only use this with award IDs. Generally these award IDs will come from GetSpendingAwardsByAgencyID

    Args:
        generated_unique_award_id: the unique id associated to the award
    """

    BASE_URL = "https://api.usaspending.gov/api/v2/awards/"
    URL = urljoin(BASE_URL, f"{args.generated_unique_award_id}/")
    try:
        response = await async_http_get(URL)
        return response.json()
    except httpx.HTTPStatusError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Received {e.response.status_code} from usaspending.gov while requesting {e.request.url}",
            )
        )
    except httpx.RequestError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Error while requesting {e.request.url}. Http Error: {e!r}",
            )
        )


class KeywordSearchArgs(BaseModel):
    keywords: List[str]
    year: int


@mcp.tool(name="SearchByKeywords")
async def search_award_by_keyword(args: KeywordSearchArgs) -> Dict[str, Any] | None:
    """
    Search USASpending.gove for details of spending awards.
    - You should only use this tool when you want to do a broad search for awards by keyword
    - Use this tool when you are looking up broad keywords.
    - Returns 20 results ordered by Award Amount
    """

    URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

    start_date = datetime(year=args.year, month=1, day=1).strftime("%Y-%m-%d")
    end_date = datetime(year=args.year, month=12, day=31).strftime("%Y-%m-%d")

    data = {
        "filters": {
            "keywords": args.keywords,
            "time_period": [{"start_date": start_date, "end_date": end_date}],
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Total Outlays",
            "Description",
            "Contract Award Type",
            "def_codes",
            "COVID-19 Obligations",
            "COVID-19 Outlays",
            "Infrastructure Obligations",
            "Infrastructure Outlays",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Start Date",
            "End Date",
            "recipient_id",
            "prime_award_recipient_id",
        ],
        "page": 1,
        "limit": 20,
        "sort": "Award Amount",
        "order": "desc",
        "subawards": False,
    }
    try:
        response = await async_http_post(URL, json=data)
        return response.json()
    except httpx.HTTPStatusError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Received {e.response.status_code} from usaspending.gov while requesting {e.request.url}",
            )
        )
    except httpx.RequestError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Error while requesting {e.request.url}. Http Error: {e!r}",
            )
        )


@mcp.tool(name="GetAgencies")
async def get_us_agencies() -> Dict[str, Any] | None:
    """Get US agencies and their ids and codes
    - Use this when you want to get a list of all the us agencies and their metadata

    Usage:
        get_us_agencies()
    """
    URL = "https://api.usaspending.gov/api/v2/references/toptier_agencies/"
    try:
        response = await async_http_get(URL)
        return response.json()
    except httpx.HTTPStatusError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Received {e.response.status_code} from usaspending.gov while requesting {e.request.url}",
            )
        )
    except httpx.RequestError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Error while requesting {e.request.url}. Http Error: {e!r}",
            )
        )

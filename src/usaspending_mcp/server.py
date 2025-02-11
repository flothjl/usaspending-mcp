from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
import mcp.types as mcp_types
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from pydantic import BaseModel, Field

from usaspending_mcp.util import async_http_get, async_http_post

mcp = FastMCP("usaspending")


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


class KeywordSearchResponse(BaseModel):
    internal_id: Optional[int]
    description: Optional[str] = Field(alias="Description")
    award_id: Optional[str] = Field(alias="Award ID")
    recipient_name: str = Field(alias="Recipient Name")
    award_amount: Optional[float] = Field(alias="Award Amount")
    total_outlays: Optional[float] = Field(alias="Total Outlays")
    awarding_agency: Optional[str] = Field(alias="Awarding Agency")
    awarding_subagency: Optional[str] = Field(alias="Awarding Sub Agency")
    start_date: Optional[str] = Field(alias="Start Date")
    end_date: Optional[str] = Field(alias="End Date")
    awarding_agency_id: Optional[int] = Field(alias="awarding_agency_id")
    generated_unique_award_id: Optional[str] = Field(alias="generated_internal_id")


@mcp.tool(name="SearchByKeywords")
async def search_award_by_keyword(
    args: KeywordSearchArgs,
) -> List[KeywordSearchResponse]:
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
        mapped = response.json().get("results", [])
        return [KeywordSearchResponse(**i) for i in mapped]
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


if __name__ == "__main__":
    mcp.run()

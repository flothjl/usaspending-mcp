# usaspending-mcp

**usaspending-mcp** is an MCP (Modular Computing Platform) server designed
to facilitate AI agents in accessing and interacting with the
[USAspending.gov](https://www.usaspending.gov/) API. This project provides tools,
endpoints, and data processing utilities to streamline the retrieval
and analysis of U.S. government spending data.

## usage with [Goose](https://github.com/block/goose)

```bash
uvx --from git+https://github.com/flothjl/usaspending-mcp@main usaspending-mcp
```

### Tools

- **GetSpendingAwardsByAgencyId**
  - Search for awards for a given agency id for a given year
- **GetAwardInfoByAwardId**
  - Get information about a given award. Requires the generated unique award ID.
- **SearchByKeywords**
  - Broad search for given keywords for a given year.
- **GetAgencies**
  - Get a list of all agencies and associated data needed for other calls (i.e. agency id)

from typing import Dict
from mcp.server.fastmcp import FastMCP
import os
from nostr_sdk import init_logger, Keys, NostrSigner, Client, EventBuilder, LogLevel

# Initialize FastMCP server
mcp = FastMCP("goostr")

GOOSTR_NSEC = os.getenv("GOOSTR_NSEC")


@mcp.tool()
async def publish_note(note: str) -> Dict[str, str]:
    """Publish a Kind 1 nostr EventBuilder

    Args:
        note: Note content
    """

    init_logger(LogLevel.INFO)

    keys = Keys.generate()
    signer = NostrSigner.keys(keys)
    client = Client(signer)

    await client.add_relay("wss://relay.damus.io")
    await client.add_relay("wss://nos.lol")

    await client.connect()

    builder = EventBuilder.text_note(note)
    output = await client.send_event_builder(builder)

    return {"npub": keys.public_key().to_bech32(), "note_id": output.id.to_bech32()}


if __name__ == "__main__":
    mcp.run(transport="stdio")

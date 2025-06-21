import os
import httpx
from fastmcp import FastMCP
from typing import Annotated
from dotenv import load_dotenv
from pydantic import Field

mcp = FastMCP(name="BarsoBotMCP")

load_dotenv()


@mcp.tool()
async def send_message(
    name: Annotated[str, Field(description="The sender name")],
    message: Annotated[str, Field(description="The message to be sent")],
) -> dict:
    """Send the given message to Yuri."""
    payload = {"name": name, "message": message}
    async with httpx.AsyncClient() as client:
        response = await client.post(os.getenv("WEBHOOK_URL"), json=payload)
        return response.json()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

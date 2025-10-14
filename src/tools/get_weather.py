"""Get current weather for a location."""

from typing import Annotated, Optional
from fastmcp import Context
from core.app import mcp
from .weather_client import WeatherGovClient
from .models import WeatherData

weather_client = WeatherGovClient()


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def get_weather(
    location: Annotated[str, "Location to get weather for (city, state format, e.g., 'Seattle, WA')"],
    ctx: Optional[Context] = None
) -> dict:
    """Get current weather for a location.

    Retrieves current weather conditions and forecast from Weather.gov API
    for a specified location. The location should be provided in 'City, State'
    format for best results.

    Args:
        location: Location to get weather for (city, state format, e.g., "Seattle, WA")
        ctx: Optional MCP context for logging

    Returns:
        Dictionary containing weather data (None values excluded):
            - location: The location name
            - temperature: Current temperature in both Fahrenheit and Celsius
            - conditions: Current weather conditions description
            - forecast: Detailed forecast for the current period
            - humidity: Current humidity percentage
            - wind: Wind speed and direction
            - timestamp: ISO 8601 timestamp of the observation
            - source: Data source (Weather.gov)
    """
    if ctx:
        await ctx.info(f"Getting weather for: {location}")

    try:
        weather_data = weather_client.get_weather_by_location(location)
        weather_obj = WeatherData(**weather_data)
        return weather_obj.to_prompt_dict()
    except Exception as e:
        error_msg = f"Error getting weather for {location}: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise RuntimeError(error_msg)

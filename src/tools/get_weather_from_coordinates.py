"""Get weather data from geographic coordinates."""

from typing import Annotated, Optional
from pydantic import Field
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
async def get_weather_from_coordinates(
    lat: Annotated[float, Field(ge=-90, le=90, description="Latitude coordinate (-90 to 90)")],
    lon: Annotated[float, Field(ge=-180, le=180, description="Longitude coordinate (-180 to 180)")],
    ctx: Optional[Context] = None
) -> dict:
    """Get weather data from latitude and longitude coordinates.

    Retrieves current weather conditions and forecast from Weather.gov API
    for specified geographic coordinates. The coordinates are validated to
    ensure they fall within valid latitude (-90 to 90) and longitude
    (-180 to 180) ranges.

    Args:
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate (-180 to 180)
        ctx: Optional MCP context for logging

    Returns:
        Dictionary containing weather data (None values excluded):
            - location: The resolved location name
            - temperature: Current temperature in both Fahrenheit and Celsius
            - conditions: Current weather conditions description
            - forecast: Detailed forecast for the current period
            - humidity: Current humidity percentage
            - wind: Wind speed and direction
            - timestamp: ISO 8601 timestamp of the observation
            - source: Data source (Weather.gov)
            - coordinates: Dict with 'lat' and 'lon' keys containing the input coordinates
    """
    if ctx:
        await ctx.info(f"Getting weather for coordinates: {lat}, {lon}")

    try:
        weather_data = weather_client.get_weather_by_coordinates(lat, lon)
        weather_obj = WeatherData(**weather_data)
        return weather_obj.to_prompt_dict()
    except Exception as e:
        error_msg = f"Error getting weather for coordinates ({lat}, {lon}): {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise RuntimeError(error_msg)

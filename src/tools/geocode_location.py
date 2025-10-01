from core.app import mcp
from fastmcp import Context
from .weather_client import WeatherGovClient
from typing import Optional, Dict, Any

weather_client = WeatherGovClient()

@mcp.tool
async def geocode_location(city: str, state: Optional[str] = None, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Convert a city name to geographic coordinates.

    Args:
        city: City name to geocode (e.g., "Seattle", "Brownwood")
        state: State code or full name (optional, e.g., "TX", "Texas", "WA")

    Returns:
        Dictionary containing:
            - city (str): The input city name
            - state (str): The resolved state/region name
            - lat (float): Latitude coordinate
            - lon (float): Longitude coordinate
    """
    if ctx:
        await ctx.info(f"Geocoding location: {city}" + (f", {state}" if state else ""))

    try:
        geocode_data = weather_client.geocode_city(city, state)
        return geocode_data
    except Exception as e:
        error_msg = f"Error geocoding location {city}: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise RuntimeError(error_msg)
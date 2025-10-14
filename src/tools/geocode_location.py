"""Convert city names to geographic coordinates."""

from typing import Annotated, Optional
from fastmcp import Context
from core.app import mcp
from .weather_client import WeatherGovClient
from .models import GeocodeData

weather_client = WeatherGovClient()


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def geocode_location(
    city: Annotated[str, "City name to geocode (e.g., 'Seattle', 'Brownwood')"],
    state: Annotated[Optional[str], "State code or full name (optional, e.g., 'TX', 'Texas', 'WA')"] = None,
    ctx: Optional[Context] = None
) -> dict:
    """Convert a city name to geographic coordinates.

    Uses the OpenStreetMap Nominatim API to convert city and state names
    into latitude and longitude coordinates. The state parameter is optional
    but recommended for more accurate results, especially for common city names.

    Args:
        city: City name to geocode (e.g., "Seattle", "Brownwood")
        state: State code or full name (optional, e.g., "TX", "Texas", "WA")
        ctx: Optional MCP context for logging

    Returns:
        Dictionary containing geocoding results (None values excluded):
            - city: The input city name
            - state: The resolved state/region name
            - lat: Latitude coordinate
            - lon: Longitude coordinate
    """
    if ctx:
        await ctx.info(f"Geocoding location: {city}" + (f", {state}" if state else ""))

    try:
        geocode_data = weather_client.geocode_city(city, state)
        geocode_obj = GeocodeData(**geocode_data)
        return geocode_obj.to_prompt_dict()
    except Exception as e:
        error_msg = f"Error geocoding location {city}: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise RuntimeError(error_msg)

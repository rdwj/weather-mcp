from core.app import mcp
from fastmcp import Context
from .weather_client import WeatherGovClient
from typing import Dict, Any

weather_client = WeatherGovClient()

@mcp.tool
async def get_weather(location: str, ctx: Context) -> Dict[str, Any]:
    """Get current weather for a location.

    Args:
        location: Location to get weather for (city, state format, e.g., "Seattle, WA")

    Returns:
        Dictionary containing:
            - location (str): The location name
            - temperature (str): Current temperature in both Fahrenheit and Celsius
            - conditions (str): Current weather conditions description
            - forecast (str): Detailed forecast for the current period
            - humidity (str): Current humidity percentage
            - wind (str): Wind speed and direction
            - timestamp (str): ISO 8601 timestamp of the observation
            - source (str): Data source (Weather.gov)
    """
    await ctx.info(f"Getting weather for: {location}")

    try:
        weather_data = weather_client.get_weather_by_location(location)
        return weather_data
    except Exception as e:
        error_msg = f"Error getting weather for {location}: {str(e)}"
        await ctx.error(error_msg)
        raise RuntimeError(error_msg)
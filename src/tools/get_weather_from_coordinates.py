from core.app import mcp
from fastmcp import Context
from .weather_client import WeatherGovClient
from typing import Dict, Any

weather_client = WeatherGovClient()

@mcp.tool
async def get_weather_from_coordinates(lat: float, lon: float, ctx: Context) -> Dict[str, Any]:
    """Get weather data from latitude and longitude coordinates.

    Args:
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate (-180 to 180)

    Returns:
        Dictionary containing:
            - location (str): The resolved location name
            - temperature (str): Current temperature in both Fahrenheit and Celsius
            - conditions (str): Current weather conditions description
            - forecast (str): Detailed forecast for the current period
            - humidity (str): Current humidity percentage
            - wind (str): Wind speed and direction
            - timestamp (str): ISO 8601 timestamp of the observation
            - source (str): Data source (Weather.gov)
            - coordinates (dict): Contains 'lat' and 'lon' keys with the input coordinates
    """
    await ctx.info(f"Getting weather for coordinates: {lat}, {lon}")

    try:
        weather_data = weather_client.get_weather_by_coordinates(lat, lon)
        return weather_data
    except Exception as e:
        error_msg = f"Error getting weather for coordinates ({lat}, {lon}): {str(e)}"
        await ctx.error(error_msg)
        raise RuntimeError(error_msg)
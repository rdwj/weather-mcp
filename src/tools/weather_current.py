"""Get current weather conditions for a location."""

from typing import Annotated, Optional, Literal
from pydantic import Field
from fastmcp import Context
from core.app import mcp
from .weather_client import WeatherGovClient


weather_client = WeatherGovClient()


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def weather_current(
    location: Annotated[
        Optional[str],
        Field(
            default=None,
            description="City and state (e.g., 'Seattle, WA', 'Austin, Texas'). Use this OR lat/lon, not both."
        )
    ] = None,
    lat: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=-90,
            le=90,
            description="Latitude (-90 to 90). Must provide lon too. Use this OR location, not both."
        )
    ] = None,
    lon: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=-180,
            le=180,
            description="Longitude (-180 to 180). Must provide lat too. Use this OR location, not both."
        )
    ] = None,
    detail_level: Annotated[
        Literal["brief", "standard", "detailed"],
        Field(
            default="standard",
            description="Response detail: 'brief' (temp+conditions only), 'standard' (adds humidity/wind), 'detailed' (adds full forecast)"
        )
    ] = "standard",
    ctx: Optional[Context] = None
) -> dict:
    """Get current weather for a US location from Weather.gov.

    Provide EITHER a location name OR coordinates (lat+lon), not both.
    Data source: National Weather Service (Weather.gov) - US locations only.

    Examples:
        - location="Seattle, WA"
        - location="Austin, Texas"
        - lat=47.6, lon=-122.3 (Seattle coordinates)

    Use detail_level to control response size:
        - "brief": Just temperature and conditions (minimal tokens)
        - "standard": Adds humidity and wind (default)
        - "detailed": Adds full forecast text
    """
    # Validate input combinations
    has_location = location is not None
    has_coords = lat is not None or lon is not None

    if has_location and has_coords:
        raise ValueError(
            "Provide either 'location' OR 'lat'+'lon', not both. "
            "Example: location='Seattle, WA' or lat=47.6, lon=-122.3"
        )

    if not has_location and not has_coords:
        raise ValueError(
            "Missing location. Provide either: "
            "location='Seattle, WA' or lat=47.6, lon=-122.3"
        )

    if has_coords and (lat is None or lon is None):
        raise ValueError(
            "Both lat and lon are required when using coordinates. "
            "Example: lat=47.6, lon=-122.3"
        )

    if ctx:
        loc_str = location if location else f"({lat}, {lon})"
        await ctx.info(f"Getting weather for: {loc_str}")

    try:
        # Get weather data
        if location:
            weather_data = weather_client.get_weather_by_location(location)
        else:
            weather_data = weather_client.get_weather_by_coordinates(lat, lon)

        # Format response based on detail level
        result = {
            "location": weather_data.get("location", location or f"{lat}, {lon}"),
            "temperature": weather_data.get("temperature", "Unknown"),
            "conditions": weather_data.get("conditions", "Unknown"),
        }

        if detail_level in ("standard", "detailed"):
            result["humidity"] = weather_data.get("humidity", "Unknown")
            result["wind"] = weather_data.get("wind", "Unknown")

        if detail_level == "detailed":
            result["forecast"] = weather_data.get("forecast", "Not available")
            result["timestamp"] = weather_data.get("timestamp")
            result["source"] = "Weather.gov (National Weather Service)"

        return result

    except ValueError as e:
        # Location-related errors - provide helpful suggestions
        error_str = str(e)
        if "not found" in error_str.lower():
            raise ValueError(
                f"Location not found: {location or f'({lat}, {lon})'}. "
                "Tips: Use 'City, State' format (e.g., 'Austin, TX'). "
                "Weather.gov only covers US locations."
            )
        raise

    except Exception as e:
        error_msg = str(e)
        loc_str = location if location else f"({lat}, {lon})"

        # Provide actionable error messages
        if "404" in error_msg or "not found" in error_msg.lower():
            raise ValueError(
                f"No weather data available for {loc_str}. "
                "This may be outside Weather.gov coverage (US only) or "
                "a very remote area. Try a nearby city."
            )
        elif "timeout" in error_msg.lower():
            raise RuntimeError(
                f"Weather.gov API timed out. The service may be slow. "
                "Please try again in a moment."
            )
        else:
            if ctx:
                await ctx.error(f"Weather error for {loc_str}: {error_msg}")
            raise RuntimeError(
                f"Unable to get weather for {loc_str}: {error_msg}"
            )

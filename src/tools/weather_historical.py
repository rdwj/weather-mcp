"""Get historical weather data for a location."""

from typing import Annotated, Optional, List, Literal
from pydantic import Field
from fastmcp import Context
from core.app import mcp
from .weather_client import WeatherGovClient
from .historical_client import NOAAHistoricalClient


weather_client = WeatherGovClient()


def _get_historical_client() -> NOAAHistoricalClient:
    """Get historical client, with helpful error if API key missing."""
    try:
        return NOAAHistoricalClient()
    except ValueError as e:
        raise ValueError(
            "Historical weather requires NOAA_CDO_TOKEN environment variable. "
            "Get a free API key at: https://www.ncei.noaa.gov/cdo-web/token"
        ) from e


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def weather_historical(
    location: Annotated[
        str,
        Field(description="City and state (e.g., 'Seattle, WA', 'Austin, Texas')")
    ],
    start_date: Annotated[
        str,
        Field(description="Start date in YYYY-MM-DD format (e.g., '2024-01-01')")
    ],
    end_date: Annotated[
        str,
        Field(description="End date in YYYY-MM-DD format (e.g., '2024-01-31'). Multi-year ranges supported.")
    ],
    measurements: Annotated[
        Optional[List[Literal["TMAX", "TMIN", "TAVG", "PRCP", "SNOW", "SNWD"]]],
        Field(
            default=None,
            description="Data types to retrieve. Default: ['TMAX', 'TMIN', 'PRCP']. Options: TMAX (high temp), TMIN (low temp), TAVG (avg temp), PRCP (precipitation), SNOW (snowfall), SNWD (snow depth)"
        )
    ] = None,
    granularity: Annotated[
        Literal["daily", "monthly", "yearly"],
        Field(
            default="daily",
            description="Output granularity. 'daily' returns each day (max 1 year range). 'monthly' returns monthly averages/totals (unlimited range). 'yearly' returns yearly summaries (unlimited range). Use monthly/yearly for multi-year analysis to avoid context overflow."
        )
    ] = "daily",
    include_observations: Annotated[
        bool,
        Field(
            default=True,
            description="If True, include the observations array. If False, return only summary statistics (reduces response size)."
        )
    ] = True,
    ctx: Optional[Context] = None
) -> dict:
    """Get historical weather data for a US location from NOAA Climate Data Online.

    Automatically finds the nearest weather station with data for your date range.
    Data source: NOAA Global Historical Climatology Network Daily (GHCND).

    IMPORTANT: Use appropriate granularity for your date range to manage context size:
        - daily: Max 1 year range (~365 observations)
        - monthly: Unlimited range (~120 observations for 10 years)
        - yearly: Unlimited range (~10 observations for 10 years)

    Examples:
        - Short range daily: location="Seattle, WA", start_date="2024-01-01", end_date="2024-12-31"
        - Multi-year monthly: location="Austin, TX", start_date="2015-01-01", end_date="2024-12-31", granularity="monthly"
        - Decade summary: location="Denver, CO", start_date="2015-01-01", end_date="2024-12-31", granularity="yearly"

    Measurement types:
        - TMAX: Daily maximum temperature
        - TMIN: Daily minimum temperature
        - TAVG: Daily average temperature
        - PRCP: Precipitation (rain, melted snow)
        - SNOW: Snowfall
        - SNWD: Snow depth on ground
    """
    if ctx:
        await ctx.info(f"Getting historical weather for {location} ({start_date} to {end_date})")

    # Default measurements
    if measurements is None:
        measurements = ["TMAX", "TMIN", "PRCP"]

    try:
        # Geocode the location first
        parts = location.split(",")
        city = parts[0].strip()
        state = parts[1].strip() if len(parts) > 1 else None

        if ctx:
            await ctx.info(f"Geocoding {city}, {state}...")

        coords = weather_client.geocode_city(city, state)
        lat, lon = coords["lat"], coords["lon"]

        if ctx:
            await ctx.info(f"Found coordinates: {lat}, {lon}. Searching for nearby stations...")

        # Get historical data
        historical_client = _get_historical_client()

        # Calculate expected chunks for progress reporting
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        years_span = (end_dt - start_dt).days / 365.25
        if ctx and years_span > 1:
            await ctx.info(f"Fetching ~{int(years_span) + 1} years of data ({granularity} granularity)...")

        data = historical_client.get_historical_by_location(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            datatypes=list(measurements),
            location_name=location,
            granularity=granularity
        )

        # Format response
        result = {
            "location": location,
            "station": data.get("station_name", "Unknown"),
            "period": f"{start_date} to {end_date}",
            "granularity": granularity,
            "measurements": list(measurements),
            "observation_count": data.get("observation_count", 0),
            "raw_daily_count": data.get("raw_daily_count", 0),
            "year_chunks_fetched": data.get("year_chunks_fetched", 1),
        }

        observations = data.get("observations", [])

        # Calculate summary statistics (only for daily data, monthly/yearly already are summaries)
        if granularity == "daily" and observations:
            result["summary"] = _calculate_summary(observations, list(measurements))

        # Include observations array if requested
        if include_observations:
            result["observations"] = observations

        result["source"] = "NOAA Climate Data Online (GHCND)"

        return result

    except ValueError as e:
        error_str = str(e)

        # Provide helpful error messages
        if "not found" in error_str.lower():
            raise ValueError(
                f"Location '{location}' not found. Use 'City, State' format "
                "(e.g., 'Austin, TX'). US locations only."
            )
        elif "no weather stations" in error_str.lower():
            raise ValueError(
                f"No historical data stations found near {location} for {start_date} to {end_date}. "
                "Try a larger city or different date range. Historical data may be limited for some areas."
            )
        elif "daily granularity limited" in error_str.lower():
            raise ValueError(
                f"Daily granularity is limited to 1 year max to avoid context overflow. "
                f"For multi-year ranges, use granularity='monthly' or granularity='yearly'."
            )
        elif "API key" in error_str.lower() or "NOAA_CDO_TOKEN" in error_str:
            raise ValueError(
                "Historical weather requires NOAA_CDO_TOKEN. "
                "Get a free key at: https://www.ncei.noaa.gov/cdo-web/token"
            )
        raise

    except Exception as e:
        if ctx:
            await ctx.error(f"Historical weather error: {str(e)}")
        raise RuntimeError(
            f"Unable to get historical weather for {location}: {str(e)}"
        )


def _calculate_summary(observations: List[dict], measurements: List[str]) -> dict:
    """Calculate summary statistics from observations."""
    summary = {}

    # Temperature summaries
    if "TMAX" in measurements:
        temps = [o["tmax"]["fahrenheit"] for o in observations if "tmax" in o]
        if temps:
            summary["temperature_high"] = {
                "max": f"{max(temps)}°F",
                "min": f"{min(temps)}°F",
                "avg": f"{sum(temps)/len(temps):.1f}°F"
            }

    if "TMIN" in measurements:
        temps = [o["tmin"]["fahrenheit"] for o in observations if "tmin" in o]
        if temps:
            summary["temperature_low"] = {
                "max": f"{max(temps)}°F",
                "min": f"{min(temps)}°F",
                "avg": f"{sum(temps)/len(temps):.1f}°F"
            }

    if "TAVG" in measurements:
        temps = [o["tavg"]["fahrenheit"] for o in observations if "tavg" in o]
        if temps:
            summary["temperature_avg"] = {
                "max": f"{max(temps)}°F",
                "min": f"{min(temps)}°F",
                "avg": f"{sum(temps)/len(temps):.1f}°F"
            }

    # Precipitation summary
    if "PRCP" in measurements:
        precip = [o["precipitation"]["inches"] for o in observations if "precipitation" in o]
        if precip:
            summary["precipitation"] = {
                "total": f"{sum(precip):.2f} inches",
                "days_with_precip": len([p for p in precip if p > 0]),
                "max_daily": f"{max(precip):.2f} inches"
            }

    # Snow summaries
    if "SNOW" in measurements:
        snow = [o.get("snowfall_mm", 0) for o in observations]
        if any(s > 0 for s in snow):
            summary["snowfall"] = {
                "total_mm": sum(snow),
                "days_with_snow": len([s for s in snow if s > 0])
            }

    return summary

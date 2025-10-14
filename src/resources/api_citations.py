from core.app import mcp


def get_citation_data(source: str) -> dict:
    """Helper function to get citation data for a specific source."""
    citations = {
        "weather": {
            "api_name": "National Weather Service API",
            "provider": "National Oceanic and Atmospheric Administration (NOAA)",
            "description": "Provides weather observations, forecasts, and alerts for the United States",
            "base_url": "https://api.weather.gov",
            "documentation_url": "https://www.weather.gov/documentation/services-web-api",
            "terms_of_use": "Public domain - free for any use",
            "rate_limits": "No authentication required. Please follow reasonable use guidelines.",
            "data_freshness": "Real-time observations updated hourly, forecasts updated multiple times daily",
            "coverage": "United States and territories only",
            "citation_text": "Weather data provided by the National Weather Service, NOAA",
            "attribution_required": False,
            "notes": "Official U.S. government weather service"
        },
        "geocode": {
            "api_name": "Nominatim API",
            "provider": "OpenStreetMap Foundation",
            "description": "Open-source geocoding service based on OpenStreetMap data",
            "base_url": "https://nominatim.openstreetmap.org",
            "documentation_url": "https://nominatim.org/release-docs/latest/",
            "terms_of_use": "Open Data Commons Open Database License (ODbL)",
            "rate_limits": "Maximum 1 request per second. No bulk geocoding without arrangement.",
            "data_freshness": "Updated continuously from OpenStreetMap contributions",
            "coverage": "Worldwide",
            "citation_text": "Geocoding by Nominatim, © OpenStreetMap contributors",
            "attribution_required": True,
            "attribution_details": "Must credit OpenStreetMap contributors when displaying results",
            "notes": "Community-maintained open data project"
        },
        "alerts": {
            "api_name": "NWS Alerts API",
            "provider": "National Weather Service, NOAA",
            "description": "Active weather watches, warnings, and advisories for the United States",
            "base_url": "https://api.weather.gov/alerts",
            "documentation_url": "https://www.weather.gov/documentation/services-web-api#/default/alerts_active",
            "terms_of_use": "Public domain - free for any use",
            "rate_limits": "No authentication required. Please cache results appropriately.",
            "data_freshness": "Real-time, updated as alerts are issued or cancelled",
            "coverage": "United States and territories",
            "citation_text": "Alert data from the National Weather Service, NOAA",
            "attribution_required": False,
            "severity_levels": ["Extreme", "Severe", "Moderate", "Minor", "Unknown"],
            "notes": "Official source for U.S. weather warnings and watches"
        }
    }
    return citations.get(source, {})


@mcp.resource("citations://weather-api")
async def get_weather_citation() -> dict:
    """Get citation information for the Weather.gov API.

    Returns:
        Dictionary containing API details, terms of use, and attribution requirements
    """
    return get_citation_data("weather")


@mcp.resource("citations://geocode-api")
async def get_geocode_citation() -> dict:
    """Get citation information for the OpenStreetMap Nominatim API.

    Returns:
        Dictionary containing API details, terms of use, and attribution requirements
    """
    return get_citation_data("geocode")


@mcp.resource("citations://all")
async def get_all_citations() -> dict:
    """Get citation information for all APIs used by this weather service.

    Returns:
        Dictionary containing citations for all data sources with attribution requirements
    """
    all_citations = {
        "weather_api": get_citation_data("weather"),
        "geocode_api": get_citation_data("geocode"),
        "alerts_api": get_citation_data("alerts"),
        "summary": {
            "attribution_statement": "Weather data from NOAA/NWS, geocoding by OpenStreetMap contributors",
            "required_attributions": [
                "When displaying geocoded locations: © OpenStreetMap contributors"
            ],
            "optional_attributions": [
                "Weather data provided by the National Weather Service"
            ]
        }
    }
    return all_citations
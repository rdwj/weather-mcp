from core.app import mcp


@mcp.resource("info://data-sources")
async def get_data_sources() -> dict:
    """Get information about all data sources used by this weather MCP server.

    Returns:
        Dictionary containing data sources, reliability, and appropriate use cases
    """
    sources_info = {
        "title": "Weather MCP Server Data Sources",
        "description": "This MCP server aggregates data from multiple authoritative weather sources",
        "last_updated": "2024-09-25",
        "sources": [
            {
                "name": "NOAA/NWS Weather Data",
                "type": "weather",
                "reliability": "Very High",
                "use_cases": [
                    "Current weather observations",
                    "7-day forecasts",
                    "Hourly forecasts",
                    "Weather alerts and warnings"
                ],
                "limitations": [
                    "U.S. and territories only",
                    "Station coverage varies by region",
                    "Rural areas may have less frequent updates"
                ],
                "update_frequency": "Hourly for observations, 2-4 times daily for forecasts"
            },
            {
                "name": "OpenStreetMap Nominatim",
                "type": "geocoding",
                "reliability": "High",
                "use_cases": [
                    "City to coordinate conversion",
                    "Address geocoding",
                    "Reverse geocoding"
                ],
                "limitations": [
                    "Accuracy varies by region",
                    "Some small towns may not be found",
                    "Rate limited to prevent abuse"
                ],
                "update_frequency": "Continuous community updates"
            }
        ],
        "data_quality_notes": {
            "accuracy": "Weather observations are from official government stations with high-quality instruments",
            "latency": "Current conditions typically 10-60 minutes behind real-time",
            "availability": "99.9% uptime for NOAA services, Nominatim availability varies",
            "forecasting": "NWS forecasts use advanced numerical weather prediction models"
        },
        "recommended_usage": {
            "general_public": "Suitable for daily planning and general weather awareness",
            "outdoor_activities": "Check multiple times for camping, hiking, sporting events",
            "travel_planning": "Good for trip planning 3-7 days in advance",
            "emergency_preparedness": "Monitor alerts resource for severe weather warnings",
            "not_recommended_for": [
                "Aviation (use official aviation weather services)",
                "Marine navigation (use marine-specific forecasts)",
                "Life-critical decisions without additional verification"
            ]
        },
        "legal_disclaimer": "This service aggregates publicly available weather data. While we strive for accuracy, weather conditions can change rapidly. Always use multiple sources and official warnings for safety-critical decisions."
    }

    return sources_info
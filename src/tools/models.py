"""Pydantic models for structured tool returns."""

from pydantic import BaseModel, Field
from typing import Optional


class Coordinates(BaseModel):
    """Geographic coordinates."""
    lat: float = Field(description="Latitude coordinate")
    lon: float = Field(description="Longitude coordinate")


class WeatherData(BaseModel):
    """Weather data response from Weather.gov API."""
    location: str = Field(description="The location name")
    temperature: str = Field(description="Current temperature in both Fahrenheit and Celsius")
    conditions: str = Field(description="Current weather conditions description")
    forecast: str = Field(description="Detailed forecast for the current period")
    humidity: str = Field(description="Current humidity percentage")
    wind: str = Field(description="Wind speed and direction")
    timestamp: str = Field(description="ISO 8601 timestamp of the observation")
    source: str = Field(description="Data source (Weather.gov)")
    coordinates: Optional[Coordinates] = Field(
        default=None,
        description="Geographic coordinates (only present when queried by coordinates)"
    )

    def to_prompt_dict(self) -> dict:
        """Serialize to dictionary for MCP prompts, excluding None values.

        Returns:
            Dictionary with None values excluded, suitable for prompt parameters
        """
        return self.model_dump(exclude_none=True, mode='json')


class GeocodeData(BaseModel):
    """Geocoding result with coordinates."""
    city: str = Field(description="The city name")
    state: str = Field(description="The resolved state/region name")
    lat: float = Field(description="Latitude coordinate")
    lon: float = Field(description="Longitude coordinate")

    def to_prompt_dict(self) -> dict:
        """Serialize to dictionary for MCP prompts, excluding None values.

        Returns:
            Dictionary with None values excluded, suitable for prompt parameters
        """
        return self.model_dump(exclude_none=True, mode='json')

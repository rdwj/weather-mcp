"""Tests for serialization utilities and None value handling."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from tools.models import WeatherData, GeocodeData, Coordinates  # type: ignore
from tools.serializers import serialize_for_prompt, serialize_model_dict  # type: ignore


def test_weather_data_to_prompt_dict_excludes_none():
    """Test that WeatherData.to_prompt_dict() excludes None values."""
    weather = WeatherData(
        location="Austin, TX",
        temperature="66.9°F (19.4°C)",
        conditions="Clear",
        forecast="Sunny throughout the day",
        humidity="45%",
        wind="N 5 mph",
        timestamp="2025-10-14T12:13:20.151883+00:00",
        source="Weather.gov",
        coordinates=None  # This should be excluded
    )

    result = weather.to_prompt_dict()

    # Verify None value is excluded
    assert "coordinates" not in result

    # Verify other fields are present
    assert result["location"] == "Austin, TX"
    assert result["temperature"] == "66.9°F (19.4°C)"
    assert result["conditions"] == "Clear"
    assert result["forecast"] == "Sunny throughout the day"
    assert result["humidity"] == "45%"
    assert result["wind"] == "N 5 mph"
    assert result["timestamp"] == "2025-10-14T12:13:20.151883+00:00"
    assert result["source"] == "Weather.gov"


def test_weather_data_to_prompt_dict_includes_coordinates():
    """Test that WeatherData.to_prompt_dict() includes coordinates when present."""
    coords = Coordinates(lat=30.2672, lon=-97.7431)
    weather = WeatherData(
        location="Austin, TX",
        temperature="66.9°F (19.4°C)",
        conditions="Clear",
        forecast="Sunny throughout the day",
        humidity="45%",
        wind="N 5 mph",
        timestamp="2025-10-14T12:13:20.151883+00:00",
        source="Weather.gov",
        coordinates=coords
    )

    result = weather.to_prompt_dict()

    # Verify coordinates are included
    assert "coordinates" in result
    assert result["coordinates"]["lat"] == 30.2672
    assert result["coordinates"]["lon"] == -97.7431


def test_geocode_data_to_prompt_dict():
    """Test that GeocodeData.to_prompt_dict() works correctly."""
    geocode = GeocodeData(
        city="Austin",
        state="Texas",
        lat=30.2672,
        lon=-97.7431
    )

    result = geocode.to_prompt_dict()

    # Verify all fields are present
    assert result["city"] == "Austin"
    assert result["state"] == "Texas"
    assert result["lat"] == 30.2672
    assert result["lon"] == -97.7431


def test_serialize_for_prompt_excludes_none():
    """Test that serialize_for_prompt() utility function excludes None values."""
    weather = WeatherData(
        location="Austin, TX",
        temperature="66.9°F (19.4°C)",
        conditions="Clear",
        forecast="Sunny throughout the day",
        humidity="45%",
        wind="N 5 mph",
        timestamp="2025-10-14T12:13:20.151883+00:00",
        source="Weather.gov",
        coordinates=None
    )

    result = serialize_for_prompt(weather)

    # Verify None value is excluded
    assert "coordinates" not in result

    # Verify other fields are present
    assert result["location"] == "Austin, TX"
    assert len(result) == 8  # Should have 8 fields, not 9


def test_serialize_model_dict_excludes_none():
    """Test that serialize_model_dict() removes None values from dictionaries."""
    data = {
        "location": "Austin, TX",
        "temperature": "66.9°F",
        "conditions": "Clear",
        "coordinates": None,
        "humidity": "45%",
        "wind": None
    }

    result = serialize_model_dict(data)

    # Verify None values are excluded
    assert "coordinates" not in result
    assert "wind" not in result

    # Verify other fields are present
    assert result["location"] == "Austin, TX"
    assert result["temperature"] == "66.9°F"
    assert result["conditions"] == "Clear"
    assert result["humidity"] == "45%"
    assert len(result) == 4


def test_serialize_model_dict_empty_dict():
    """Test that serialize_model_dict() handles empty dictionaries."""
    result = serialize_model_dict({})
    assert result == {}


def test_serialize_model_dict_all_none():
    """Test that serialize_model_dict() handles dictionaries with all None values."""
    data = {"a": None, "b": None, "c": None}
    result = serialize_model_dict(data)
    assert result == {}


def test_weather_data_model_dump_default_includes_none():
    """Test that default model_dump() includes None values (for comparison)."""
    weather = WeatherData(
        location="Austin, TX",
        temperature="66.9°F (19.4°C)",
        conditions="Clear",
        forecast="Sunny throughout the day",
        humidity="45%",
        wind="N 5 mph",
        timestamp="2025-10-14T12:13:20.151883+00:00",
        source="Weather.gov",
        coordinates=None
    )

    # Default model_dump() should include None
    result = weather.model_dump()
    assert "coordinates" in result
    assert result["coordinates"] is None

    # to_prompt_dict() should exclude None
    result_filtered = weather.to_prompt_dict()
    assert "coordinates" not in result_filtered

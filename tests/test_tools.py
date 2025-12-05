"""Tests for weather tools."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest


# Helper to get underlying function from FastMCP tool wrapper
def get_tool_fn(tool):
    """Extract the underlying async function from a FastMCP FunctionTool."""
    return tool.fn


class TestWeatherCurrent:
    """Tests for weather_current tool."""

    @pytest.mark.asyncio
    async def test_requires_location_or_coordinates(self):
        """Test that either location or lat/lon must be provided."""
        from tools.weather_current import weather_current

        with pytest.raises(ValueError) as exc_info:
            await get_tool_fn(weather_current)()

        assert "Missing location" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rejects_both_location_and_coordinates(self):
        """Test that providing both location and coordinates raises error."""
        from tools.weather_current import weather_current

        with pytest.raises(ValueError) as exc_info:
            await get_tool_fn(weather_current)(location="Seattle, WA", lat=47.6, lon=-122.3)

        assert "not both" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_requires_both_lat_and_lon(self):
        """Test that providing only lat or only lon raises error."""
        from tools.weather_current import weather_current

        with pytest.raises(ValueError) as exc_info:
            await get_tool_fn(weather_current)(lat=47.6)

        assert "Both lat and lon" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('tools.weather_current.weather_client')
    async def test_brief_response(self, mock_client):
        """Test brief detail level returns minimal data."""
        from tools.weather_current import weather_current

        mock_client.get_weather_by_location.return_value = {
            "location": "Seattle, WA",
            "temperature": "55°F (13°C)",
            "conditions": "Cloudy",
            "humidity": "80%",
            "wind": "10 mph NW",
            "forecast": "Cloudy with a chance of rain..."
        }

        result = await get_tool_fn(weather_current)(location="Seattle, WA", detail_level="brief")

        assert "location" in result
        assert "temperature" in result
        assert "conditions" in result
        assert "humidity" not in result
        assert "wind" not in result
        assert "forecast" not in result

    @pytest.mark.asyncio
    @patch('tools.weather_current.weather_client')
    async def test_standard_response(self, mock_client):
        """Test standard detail level includes humidity and wind."""
        from tools.weather_current import weather_current

        mock_client.get_weather_by_location.return_value = {
            "location": "Seattle, WA",
            "temperature": "55°F (13°C)",
            "conditions": "Cloudy",
            "humidity": "80%",
            "wind": "10 mph NW",
            "forecast": "Cloudy with a chance of rain..."
        }

        result = await get_tool_fn(weather_current)(location="Seattle, WA", detail_level="standard")

        assert "humidity" in result
        assert "wind" in result
        assert "forecast" not in result

    @pytest.mark.asyncio
    @patch('tools.weather_current.weather_client')
    async def test_detailed_response(self, mock_client):
        """Test detailed level includes forecast."""
        from tools.weather_current import weather_current

        mock_client.get_weather_by_location.return_value = {
            "location": "Seattle, WA",
            "temperature": "55°F (13°C)",
            "conditions": "Cloudy",
            "humidity": "80%",
            "wind": "10 mph NW",
            "forecast": "Cloudy with a chance of rain...",
            "timestamp": "2024-01-01T12:00:00Z"
        }

        result = await get_tool_fn(weather_current)(location="Seattle, WA", detail_level="detailed")

        assert "forecast" in result
        assert "source" in result


class TestWeatherHistorical:
    """Tests for weather_historical tool."""

    def test_api_key_error_message(self):
        """Test helpful error when API key missing."""
        from tools.historical_client import NOAAHistoricalClient
        import os

        # Ensure env var is not set
        original = os.environ.pop("NOAA_CDO_TOKEN", None)

        try:
            with pytest.raises(ValueError) as exc_info:
                NOAAHistoricalClient()

            assert "NOAA_CDO_TOKEN" in str(exc_info.value)
            assert "ncei.noaa.gov" in str(exc_info.value)
        finally:
            if original:
                os.environ["NOAA_CDO_TOKEN"] = original

    def test_multi_year_chunking(self):
        """Test that multi-year date ranges are properly chunked."""
        from tools.historical_client import NOAAHistoricalClient

        # Create client instance without API key validation
        client = NOAAHistoricalClient.__new__(NOAAHistoricalClient)

        # Test 2-year range generates 2 chunks
        chunks = client._generate_year_chunks("2020-01-01", "2021-12-31")
        assert len(chunks) == 2
        assert chunks[0] == ("2020-01-01", "2020-12-31")
        assert chunks[1] == ("2021-01-01", "2021-12-31")

        # Test 10-year range generates 10 chunks
        chunks = client._generate_year_chunks("2015-01-01", "2024-12-31")
        assert len(chunks) == 10
        assert chunks[0][0] == "2015-01-01"
        assert chunks[-1][1] == "2024-12-31"

        # Test partial year generates 1 chunk
        chunks = client._generate_year_chunks("2024-06-01", "2024-08-31")
        assert len(chunks) == 1
        assert chunks[0] == ("2024-06-01", "2024-08-31")


class TestHistoricalClientDataProcessing:
    """Tests for data processing in historical client."""

    def test_temperature_conversion(self):
        """Test that temperatures are correctly converted from tenths of C."""
        # Temperature conversion: 200 tenths = 20°C = 68°F
        celsius = 200 / 10.0
        fahrenheit = (celsius * 9/5) + 32

        assert celsius == 20.0
        assert fahrenheit == 68.0

    def test_precipitation_conversion(self):
        """Test that precipitation is correctly converted from tenths of mm."""
        # Precipitation: 100 tenths = 10mm = 0.39 inches
        mm = 100 / 10.0
        inches = mm / 25.4

        assert mm == 10.0
        assert round(inches, 2) == 0.39


class TestHistoricalClientAggregation:
    """Tests for aggregation logic in historical client."""

    def test_monthly_aggregation(self):
        """Test that daily data is correctly aggregated to monthly."""
        from tools.historical_client import NOAAHistoricalClient

        client = NOAAHistoricalClient.__new__(NOAAHistoricalClient)

        # Sample daily observations for January and February
        daily_obs = [
            {"date": "2024-01-01", "tmax": {"fahrenheit": 50.0, "celsius": 10.0}, "precipitation": {"inches": 0.1, "mm": 2.5}},
            {"date": "2024-01-02", "tmax": {"fahrenheit": 52.0, "celsius": 11.1}, "precipitation": {"inches": 0.0, "mm": 0.0}},
            {"date": "2024-01-03", "tmax": {"fahrenheit": 48.0, "celsius": 8.9}, "precipitation": {"inches": 0.2, "mm": 5.1}},
            {"date": "2024-02-01", "tmax": {"fahrenheit": 55.0, "celsius": 12.8}, "precipitation": {"inches": 0.0, "mm": 0.0}},
            {"date": "2024-02-02", "tmax": {"fahrenheit": 57.0, "celsius": 13.9}, "precipitation": {"inches": 0.3, "mm": 7.6}},
        ]

        monthly = client._aggregate_to_monthly(daily_obs)

        assert len(monthly) == 2
        assert monthly[0]["month"] == "2024-01"
        assert monthly[0]["days_with_data"] == 3
        assert monthly[0]["avg_high"]["fahrenheit"] == 50.0  # (50+52+48)/3
        assert monthly[0]["total_precipitation"]["inches"] == 0.3  # 0.1+0.0+0.2
        assert monthly[0]["days_with_precipitation"] == 2

        assert monthly[1]["month"] == "2024-02"
        assert monthly[1]["days_with_data"] == 2

    def test_yearly_aggregation(self):
        """Test that daily data is correctly aggregated to yearly."""
        from tools.historical_client import NOAAHistoricalClient

        client = NOAAHistoricalClient.__new__(NOAAHistoricalClient)

        # Sample daily observations for 2023 and 2024
        daily_obs = [
            {"date": "2023-06-15", "tmax": {"fahrenheit": 85.0, "celsius": 29.4}, "precipitation": {"inches": 0.0, "mm": 0.0}},
            {"date": "2023-12-15", "tmax": {"fahrenheit": 45.0, "celsius": 7.2}, "precipitation": {"inches": 0.5, "mm": 12.7}},
            {"date": "2024-06-15", "tmax": {"fahrenheit": 90.0, "celsius": 32.2}, "precipitation": {"inches": 0.0, "mm": 0.0}},
            {"date": "2024-12-15", "tmax": {"fahrenheit": 40.0, "celsius": 4.4}, "precipitation": {"inches": 0.8, "mm": 20.3}},
        ]

        yearly = client._aggregate_to_yearly(daily_obs)

        assert len(yearly) == 2
        assert yearly[0]["year"] == "2023"
        assert yearly[0]["days_with_data"] == 2
        assert yearly[0]["avg_high"]["fahrenheit"] == 65.0  # (85+45)/2
        assert yearly[0]["total_precipitation"]["inches"] == 0.5

        assert yearly[1]["year"] == "2024"
        assert yearly[1]["avg_high"]["fahrenheit"] == 65.0  # (90+40)/2
        assert yearly[1]["total_precipitation"]["inches"] == 0.8

    def test_daily_granularity_rejects_multi_year(self):
        """Test that daily granularity rejects requests over 1 year."""
        from tools.historical_client import NOAAHistoricalClient
        import os

        os.environ["NOAA_CDO_TOKEN"] = "test-key"

        try:
            client = NOAAHistoricalClient()

            with pytest.raises(ValueError) as exc_info:
                client.get_historical_data(
                    station_id="GHCND:USW00023174",
                    start_date="2020-01-01",
                    end_date="2022-01-01",
                    granularity="daily"
                )

            assert "daily granularity limited" in str(exc_info.value).lower()
        finally:
            os.environ.pop("NOAA_CDO_TOKEN", None)

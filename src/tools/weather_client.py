import json
from typing import Dict, Any, Optional, Tuple
import urllib.request
import urllib.parse
import urllib.error


class WeatherGovClient:
    def __init__(self):
        self.base_url = "https://api.weather.gov"
        self.geocode_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            "User-Agent": "MCP-Weather-Server/1.0",
            "Accept": "application/geo+json"
        }

    def geocode_city(self, city: str, state: Optional[str] = None) -> Dict[str, Any]:
        query = f"{city}, {state}" if state else city
        params = urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "limit": "1",
            "countrycodes": "us"
        })

        try:
            req = urllib.request.Request(
                f"{self.geocode_url}?{params}",
                headers={"User-Agent": self.headers["User-Agent"]}
            )
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            if not data or len(data) == 0:
                raise ValueError(f"Location not found: {query}")

            result = data[0]
            return {
                "city": city,
                "state": state or result["display_name"].split(",")[1].strip() if "," in result["display_name"] else "Unknown",
                "lat": float(result["lat"]),
                "lon": float(result["lon"])
            }
        except urllib.error.URLError as e:
            raise RuntimeError(f"Geocoding error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Geocoding error: {str(e)}")

    def get_weather_by_location(self, location: str) -> Dict[str, Any]:
        parts = location.split(",")
        city = parts[0].strip()
        state = parts[1].strip() if len(parts) > 1 else None

        coords = self.geocode_city(city, state)
        return self.get_weather_by_coordinates(coords["lat"], coords["lon"], location)

    def get_weather_by_coordinates(self, lat: float, lon: float, location_name: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Get grid point data
            point_url = f"{self.base_url}/points/{lat:.4f},{lon:.4f}"
            req = urllib.request.Request(point_url, headers=self.headers)

            with urllib.request.urlopen(req) as response:
                point_data = json.loads(response.read().decode())

            forecast_url = point_data["properties"]["forecast"]
            station_url = point_data["properties"]["observationStations"]

            # Get current observations from nearest station
            req = urllib.request.Request(station_url, headers=self.headers)
            with urllib.request.urlopen(req) as response:
                stations_data = json.loads(response.read().decode())

            if stations_data["features"] and len(stations_data["features"]) > 0:
                station_id = stations_data["features"][0]["properties"]["stationIdentifier"]
                obs_url = f"{self.base_url}/stations/{station_id}/observations/latest"

                req = urllib.request.Request(obs_url, headers=self.headers)
                with urllib.request.urlopen(req) as response:
                    obs_data = json.loads(response.read().decode())

                # Get forecast
                req = urllib.request.Request(forecast_url, headers=self.headers)
                with urllib.request.urlopen(req) as response:
                    forecast_data = json.loads(response.read().decode())

                obs = obs_data["properties"]
                forecast = forecast_data["properties"]["periods"][0]

                result = {
                    "location": location_name or f"{point_data['properties']['relativeLocation']['properties']['city']}, {point_data['properties']['relativeLocation']['properties']['state']}",
                    "temperature": self._format_temperature(obs.get("temperature")),
                    "conditions": obs.get("textDescription", "Unknown"),
                    "forecast": forecast["detailedForecast"],
                    "humidity": self._format_humidity(obs.get("relativeHumidity")),
                    "wind": self._format_wind(obs.get("windSpeed"), obs.get("windDirection")),
                    "timestamp": self._get_timestamp(),
                    "source": "Weather.gov"
                }

                if not location_name:
                    result["coordinates"] = {"lat": lat, "lon": lon}

                return result

            raise RuntimeError("No weather stations found for this location")

        except urllib.error.URLError as e:
            raise RuntimeError(f"Weather data error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Weather data error: {str(e)}")

    def _format_temperature(self, temp: Optional[Dict[str, Any]]) -> str:
        if not temp or "value" not in temp:
            return "Unknown"
        celsius = temp["value"]
        if celsius is None:
            return "Unknown"
        fahrenheit = (celsius * 9/5) + 32
        return f"{fahrenheit:.1f}°F ({celsius:.1f}°C)"

    def _format_humidity(self, humidity: Optional[Dict[str, Any]]) -> str:
        if not humidity or "value" not in humidity:
            return "Unknown"
        value = humidity["value"]
        if value is None:
            return "Unknown"
        return f"{value:.1f}%"

    def _format_wind(self, speed: Optional[Dict[str, Any]], direction: Optional[Dict[str, Any]]) -> str:
        if not speed or "value" not in speed:
            return "Unknown"
        speed_value = speed["value"]
        if speed_value is None:
            return "Unknown"
        mph = speed_value * 0.621371
        dir_str = f"from {direction['value']}°" if direction and "value" in direction and direction["value"] is not None else ""
        return f"{mph:.1f} mph {dir_str}".strip()

    def _get_timestamp(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
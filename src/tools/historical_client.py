"""NOAA Climate Data Online (CDO) API client for historical weather data."""

import json
import os
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict


class NOAAHistoricalClient:
    """Client for NOAA Climate Data Online API v2.

    Provides access to historical weather observations from NOAA's
    extensive network of weather stations. Requires a free API token
    from https://www.ncei.noaa.gov/cdo-web/token

    Rate limits: 5 requests/second, 10,000 requests/day per token.
    """

    BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"

    # Common data types for weather observations
    DATATYPES = {
        "TMAX": "Maximum temperature (tenths of °C)",
        "TMIN": "Minimum temperature (tenths of °C)",
        "TAVG": "Average temperature (tenths of °C)",
        "PRCP": "Precipitation (tenths of mm)",
        "SNOW": "Snowfall (mm)",
        "SNWD": "Snow depth (mm)",
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the NOAA CDO client.

        Args:
            api_key: NOAA CDO API token. If not provided, reads from
                     NOAA_CDO_TOKEN environment variable.
        """
        self.api_key = api_key or os.environ.get("NOAA_CDO_TOKEN")
        if not self.api_key:
            raise ValueError(
                "NOAA CDO API key required. Set NOAA_CDO_TOKEN environment "
                "variable or request a free token at: "
                "https://www.ncei.noaa.gov/cdo-web/token"
            )

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an authenticated request to the CDO API.

        Args:
            endpoint: API endpoint (e.g., "/stations", "/data")
            params: Query parameters

        Returns:
            JSON response as dictionary
        """
        url = f"{self.BASE_URL}{endpoint}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        req = urllib.request.Request(
            url,
            headers={
                "token": self.api_key,
                "Accept": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise ValueError(
                    "Invalid NOAA CDO API key. Request a free token at: "
                    "https://www.ncei.noaa.gov/cdo-web/token"
                )
            elif e.code == 429:
                raise RuntimeError(
                    "NOAA API rate limit exceeded (5 req/sec or 10,000/day). "
                    "Please wait and try again."
                )
            else:
                raise RuntimeError(f"NOAA API error (HTTP {e.code}): {e.reason}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error connecting to NOAA API: {str(e)}")

    def find_stations(
        self,
        lat: float,
        lon: float,
        radius_km: float = 50,
        start_date: str = None,
        end_date: str = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find weather stations near a location.

        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            radius_km: Search radius in kilometers (default 50)
            start_date: Filter stations with data from this date (YYYY-MM-DD)
            end_date: Filter stations with data until this date (YYYY-MM-DD)
            limit: Maximum number of stations to return

        Returns:
            List of station dictionaries with id, name, distance info
        """
        # Convert km to degrees (approximate)
        extent_deg = radius_km / 111.0

        params = {
            "datasetid": "GHCND",
            "extent": f"{lat-extent_deg},{lon-extent_deg},{lat+extent_deg},{lon+extent_deg}",
            "limit": limit,
            "sortfield": "name"
        }

        if start_date:
            params["startdate"] = start_date
        if end_date:
            params["enddate"] = end_date

        response = self._make_request("/stations", params)

        if "results" not in response:
            return []

        stations = []
        for station in response.get("results", []):
            stations.append({
                "station_id": station["id"],
                "name": station["name"],
                "latitude": station.get("latitude"),
                "longitude": station.get("longitude"),
                "elevation_m": station.get("elevation"),
                "min_date": station.get("mindate"),
                "max_date": station.get("maxdate")
            })

        return stations

    def _generate_year_chunks(self, start_date: str, end_date: str) -> List[tuple]:
        """Generate 1-year chunks for a date range.

        The NOAA CDO API only allows 1 year max per request, so we need to
        chunk longer ranges into multiple requests.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of (chunk_start, chunk_end) tuples as YYYY-MM-DD strings
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        chunks = []
        current_start = start

        while current_start <= end:
            # End of this chunk is either 1 year later or the final end date
            chunk_end = min(current_start + relativedelta(years=1) - timedelta(days=1), end)
            chunks.append((
                current_start.strftime("%Y-%m-%d"),
                chunk_end.strftime("%Y-%m-%d")
            ))
            # Next chunk starts the day after this one ends
            current_start = chunk_end + timedelta(days=1)

        return chunks

    def _fetch_single_year(
        self,
        station_id: str,
        start_date: str,
        end_date: str,
        datatypes: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch data for a single year chunk (max 365 days).

        Args:
            station_id: NOAA station ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), must be within 1 year of start
            datatypes: List of data types to fetch

        Returns:
            List of raw observation records from the API
        """
        all_results = []
        offset = 0
        limit = 1000  # API max per request

        while True:
            params = {
                "datasetid": "GHCND",
                "stationid": station_id,
                "startdate": start_date,
                "enddate": end_date,
                "datatypeid": ",".join(datatypes),
                "units": "metric",
                "limit": limit,
                "offset": offset
            }

            response = self._make_request("/data", params)

            results = response.get("results", [])
            if not results:
                break

            all_results.extend(results)

            # Check if there are more pages
            metadata = response.get("metadata", {}).get("resultset", {})
            total_count = metadata.get("count", 0)

            if offset + limit >= total_count:
                break

            offset += limit

        return all_results

    def _parse_observations(self, raw_results: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """Parse raw API results into grouped observations by date.

        Args:
            raw_results: Raw observation records from the API

        Returns:
            Dictionary keyed by date with parsed observation values
        """
        by_date = {}

        for obs in raw_results:
            date = obs["date"][:10]  # Extract YYYY-MM-DD
            if date not in by_date:
                by_date[date] = {"date": date}

            datatype = obs["datatype"]
            value = obs["value"]

            # Convert values to human-readable format
            if datatype in ["TMAX", "TMIN", "TAVG"]:
                # API returns tenths of degrees when units=metric
                celsius = value / 10.0
                fahrenheit = (celsius * 9/5) + 32
                by_date[date][datatype.lower()] = {
                    "celsius": round(celsius, 1),
                    "fahrenheit": round(fahrenheit, 1)
                }
            elif datatype == "PRCP":
                # API returns tenths of mm
                mm = value / 10.0
                inches = mm / 25.4
                by_date[date]["precipitation"] = {
                    "mm": round(mm, 1),
                    "inches": round(inches, 2)
                }
            elif datatype == "SNOW":
                by_date[date]["snowfall_mm"] = value
            elif datatype == "SNWD":
                by_date[date]["snow_depth_mm"] = value

        return by_date

    def _aggregate_to_monthly(self, daily_observations: List[Dict]) -> List[Dict]:
        """Aggregate daily observations to monthly summaries.

        Args:
            daily_observations: List of daily observation dicts with 'date' key

        Returns:
            List of monthly summary dicts
        """
        by_month = defaultdict(list)

        for obs in daily_observations:
            month_key = obs["date"][:7]  # YYYY-MM
            by_month[month_key].append(obs)

        monthly = []
        for month_key in sorted(by_month.keys()):
            days = by_month[month_key]
            summary = {"month": month_key, "days_with_data": len(days)}

            # Aggregate temperatures
            for temp_key, label in [("tmax", "avg_high"), ("tmin", "avg_low"), ("tavg", "avg_temp")]:
                temps_f = [d[temp_key]["fahrenheit"] for d in days if temp_key in d]
                temps_c = [d[temp_key]["celsius"] for d in days if temp_key in d]
                if temps_f:
                    summary[label] = {
                        "fahrenheit": round(sum(temps_f) / len(temps_f), 1),
                        "celsius": round(sum(temps_c) / len(temps_c), 1)
                    }

            # Aggregate precipitation (sum for month)
            precip_in = [d["precipitation"]["inches"] for d in days if "precipitation" in d]
            precip_mm = [d["precipitation"]["mm"] for d in days if "precipitation" in d]
            if precip_in:
                summary["total_precipitation"] = {
                    "inches": round(sum(precip_in), 2),
                    "mm": round(sum(precip_mm), 1)
                }
                summary["days_with_precipitation"] = len([p for p in precip_in if p > 0])

            # Aggregate snowfall (sum for month)
            snow = [d.get("snowfall_mm", 0) for d in days]
            if any(s > 0 for s in snow):
                summary["total_snowfall_mm"] = sum(snow)
                summary["days_with_snow"] = len([s for s in snow if s > 0])

            monthly.append(summary)

        return monthly

    def _aggregate_to_yearly(self, daily_observations: List[Dict]) -> List[Dict]:
        """Aggregate daily observations to yearly summaries.

        Args:
            daily_observations: List of daily observation dicts with 'date' key

        Returns:
            List of yearly summary dicts
        """
        by_year = defaultdict(list)

        for obs in daily_observations:
            year_key = obs["date"][:4]  # YYYY
            by_year[year_key].append(obs)

        yearly = []
        for year_key in sorted(by_year.keys()):
            days = by_year[year_key]
            summary = {"year": year_key, "days_with_data": len(days)}

            # Aggregate temperatures
            for temp_key, label in [("tmax", "avg_high"), ("tmin", "avg_low"), ("tavg", "avg_temp")]:
                temps_f = [d[temp_key]["fahrenheit"] for d in days if temp_key in d]
                temps_c = [d[temp_key]["celsius"] for d in days if temp_key in d]
                if temps_f:
                    summary[label] = {
                        "fahrenheit": round(sum(temps_f) / len(temps_f), 1),
                        "celsius": round(sum(temps_c) / len(temps_c), 1)
                    }
                    # Also include min/max for the year
                    summary[f"{label}_range"] = {
                        "min_f": round(min(temps_f), 1),
                        "max_f": round(max(temps_f), 1)
                    }

            # Aggregate precipitation (sum for year)
            precip_in = [d["precipitation"]["inches"] for d in days if "precipitation" in d]
            precip_mm = [d["precipitation"]["mm"] for d in days if "precipitation" in d]
            if precip_in:
                summary["total_precipitation"] = {
                    "inches": round(sum(precip_in), 2),
                    "mm": round(sum(precip_mm), 1)
                }
                summary["days_with_precipitation"] = len([p for p in precip_in if p > 0])

            # Aggregate snowfall (sum for year)
            snow = [d.get("snowfall_mm", 0) for d in days]
            if any(s > 0 for s in snow):
                summary["total_snowfall_mm"] = sum(snow)
                summary["days_with_snow"] = len([s for s in snow if s > 0])

            yearly.append(summary)

        return yearly

    def get_historical_data(
        self,
        station_id: str,
        start_date: str,
        end_date: str,
        datatypes: Optional[List[str]] = None,
        granularity: Literal["daily", "monthly", "yearly"] = "daily"
    ) -> Dict[str, Any]:
        """Get historical weather data from a station.

        Automatically handles multi-year requests by chunking into 1-year
        segments (the NOAA API limit) and aggregating results.

        Args:
            station_id: NOAA station ID (e.g., "GHCND:USW00023174")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            datatypes: List of data types (default: TMAX, TMIN, PRCP)
            granularity: Output granularity - "daily" (max 1 year), "monthly", or "yearly"

        Returns:
            Dictionary with station info and observations

        Raises:
            ValueError: If daily granularity requested for >1 year range
        """
        if datatypes is None:
            datatypes = ["TMAX", "TMIN", "PRCP"]

        # Validate date range for daily granularity
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days_span = (end - start).days

        if granularity == "daily" and days_span > 365:
            raise ValueError(
                f"Daily granularity limited to 1 year max ({days_span} days requested). "
                f"Use granularity='monthly' or 'yearly' for longer ranges to avoid context overflow."
            )

        # Generate year chunks for the date range
        chunks = self._generate_year_chunks(start_date, end_date)

        # Fetch data for each chunk
        all_raw_results = []
        for chunk_start, chunk_end in chunks:
            results = self._fetch_single_year(
                station_id=station_id,
                start_date=chunk_start,
                end_date=chunk_end,
                datatypes=datatypes
            )
            all_raw_results.extend(results)

        if not all_raw_results:
            return {
                "station_id": station_id,
                "start_date": start_date,
                "end_date": end_date,
                "granularity": granularity,
                "observations": [],
                "message": "No data available for this station and date range"
            }

        # Parse and group all observations by date
        by_date = self._parse_observations(all_raw_results)
        daily_observations = sorted(by_date.values(), key=lambda x: x["date"])

        # Apply aggregation based on granularity
        if granularity == "monthly":
            observations = self._aggregate_to_monthly(daily_observations)
        elif granularity == "yearly":
            observations = self._aggregate_to_yearly(daily_observations)
        else:
            observations = daily_observations

        return {
            "station_id": station_id,
            "start_date": start_date,
            "end_date": end_date,
            "granularity": granularity,
            "data_types": datatypes,
            "observation_count": len(observations),
            "raw_daily_count": len(daily_observations),
            "year_chunks_fetched": len(chunks),
            "observations": observations
        }

    def get_historical_by_location(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        datatypes: Optional[List[str]] = None,
        location_name: Optional[str] = None,
        granularity: Literal["daily", "monthly", "yearly"] = "daily"
    ) -> Dict[str, Any]:
        """Get historical weather data for coordinates, auto-discovering station.

        Finds the nearest weather station with data for the requested period
        and returns historical observations.

        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            datatypes: List of data types (default: TMAX, TMIN, PRCP)
            location_name: Optional friendly name for the location
            granularity: Output granularity - "daily" (max 1 year), "monthly", or "yearly"

        Returns:
            Dictionary with location, station info, and observations
        """
        # Find nearby stations with data for this period
        stations = self.find_stations(
            lat=lat,
            lon=lon,
            radius_km=100,
            start_date=start_date,
            end_date=end_date,
            limit=5
        )

        if not stations:
            raise ValueError(
                f"No weather stations found within 100km of coordinates ({lat}, {lon}) "
                f"with data for {start_date} to {end_date}. "
                "Try a different location or date range."
            )

        # Try stations until we get data
        last_error = None
        for station in stations:
            try:
                data = self.get_historical_data(
                    station_id=station["station_id"],
                    start_date=start_date,
                    end_date=end_date,
                    datatypes=datatypes,
                    granularity=granularity
                )

                if data.get("observations"):
                    data["location"] = location_name or f"{lat}, {lon}"
                    data["station_name"] = station["name"]
                    data["station_coordinates"] = {
                        "lat": station["latitude"],
                        "lon": station["longitude"]
                    }
                    return data

            except Exception as e:
                last_error = e
                continue

        # No station had data
        raise ValueError(
            f"Found {len(stations)} stations near ({lat}, {lon}) but none had "
            f"data for {start_date} to {end_date}. Try a different date range. "
            f"Last error: {last_error}"
        )

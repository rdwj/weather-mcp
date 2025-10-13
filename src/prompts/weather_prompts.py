"""Weather-related prompt templates for MCP clients."""

from pydantic import Field
from core.app import mcp


@mcp.prompt
def weather_report(
    weather_data: dict = Field(
        description="Weather data as a dictionary containing current conditions"
    ),
    output_format: str = "narrative",
    output_schema: str = ""
) -> str:
    """Generate a professional weather report from current conditions.

    Creates an informative weather report with current conditions, temperature
    analysis, wind/humidity details, and practical recommendations for outdoor
    activities and clothing.

    Args:
        weather_data: Weather data as a dictionary containing current conditions
        output_format: Desired output format (e.g., 'narrative', 'structured', 'brief'). Defaults to 'narrative'.
        output_schema: Optional format example showing desired output structure. Example: {"summary": "text", "temperature": "number"}
    """
    schema_section = ""
    if output_schema:
        schema_section = f"\n\nWhen generating structured output, follow this format example:\n{output_schema}"

    return f"""Given the following weather data:
{weather_data}

Generate a professional weather report that includes:
- Current conditions summary in natural language
- Temperature analysis with context (e.g., "cooler than average", "typical for this time of year")
- Wind and humidity details with practical implications
- Visibility and air quality if mentioned in conditions
- Practical recommendations for outdoor activities
- Appropriate clothing suggestions

Output format: {output_format}

The report should be informative yet accessible to a general audience.
Use clear, concise language and avoid excessive technical jargon.
Include relevant safety advisories if severe conditions are present.{schema_section}"""


@mcp.prompt
def daily_forecast_brief(
    current_weather: dict = Field(
        description="Current weather conditions as a dictionary"
    ),
    forecast_data: dict = Field(
        description="Forecast data as a dictionary with hourly/daily predictions"
    ),
    target_audience: str = "general public"
) -> str:
    """Create a daily weather briefing from current conditions and forecast.

    Produces a comprehensive daily briefing with morning conditions, day progression,
    afternoon/evening outlook, planning guidance, and tomorrow's preview.

    Args:
        current_weather: Current weather conditions as a dictionary
        forecast_data: Forecast data as a dictionary with hourly/daily predictions
        target_audience: Target audience for the briefing (e.g., 'general public', 'commuters', 'outdoor workers'). Defaults to 'general public'.
    """
    return f"""Using the current weather conditions and forecast data:

Current Conditions:
{current_weather}

Forecast Information:
{forecast_data}

Create a comprehensive daily weather briefing that includes:

1. MORNING BRIEFING:
   - Current conditions at start of day
   - Morning commute considerations
   - Sunrise time and conditions (if available)

2. DAY PROGRESSION:
   - How conditions will change throughout the day
   - Temperature highs and when they'll occur
   - Any weather system movements

3. AFTERNOON/EVENING:
   - Peak temperature timing
   - Evening commute weather
   - Sunset conditions (if available)

4. PLANNING GUIDANCE:
   - Best times for outdoor activities
   - Windows to avoid if severe weather expected
   - Clothing recommendations for different parts of day

5. TOMORROW'S PREVIEW:
   - Brief look at next day's expected conditions
   - Any significant changes coming

Audience: {target_audience}

The briefing should be practical and actionable, helping people plan their day
effectively. Include specific times when relevant and highlight any significant
weather changes that might affect plans."""


@mcp.prompt
def weather_comparison(
    locations_data: dict = Field(
        description="Weather data for multiple locations as a dictionary with location names as keys"
    ),
    comparison_style: str = "detailed"
) -> str:
    """Compare weather conditions between multiple locations.

    Analyzes and compares temperature, weather conditions, wind/humidity,
    and provides travel considerations and recommendations for different locations.

    Args:
        locations_data: Weather data for multiple locations as a dictionary with location names as keys
        comparison_style: Style of comparison (e.g., 'detailed', 'summary', 'table', 'highlights'). Defaults to 'detailed'.
    """
    return f"""Compare the weather conditions between the following locations:

{locations_data}

Provide a comprehensive comparison that includes:

1. TEMPERATURE COMPARISON:
   - Which location is warmest/coolest
   - Temperature differences between locations
   - Feels-like temperature variations

2. WEATHER CONDITIONS:
   - Current sky conditions at each location
   - Precipitation differences
   - Which location has the best/worst weather

3. WIND & HUMIDITY:
   - Wind speed variations
   - Humidity comfort levels
   - Impact on outdoor activities

4. TRAVEL CONSIDERATIONS:
   - Best location for specific activities (beach, hiking, sports, etc.)
   - Weather-related travel advisories
   - Driving or flying conditions between locations

5. RECOMMENDATIONS:
   - Which location is preferable for various activities
   - Timing considerations (if forecasts are available)
   - Special considerations for each location

Output Style: {comparison_style}

Present the comparison in a clear, organized manner that makes it easy to
understand the differences and make decisions based on weather preferences."""


@mcp.prompt
def severe_weather_alert(
    weather_data: dict = Field(
        description="Current weather data as a dictionary"
    ),
    weather_alerts: dict | str = "None"
) -> str:
    """Analyze weather data and alerts for severe or concerning conditions.

    Evaluates immediate hazards, health/safety concerns, travel impacts,
    and provides recommended actions with severity classification.

    Args:
        weather_data: Current weather data as a dictionary
        weather_alerts: Active weather alerts as a dictionary or string. Use 'None' if no alerts. Defaults to 'None'.
    """
    return f"""Analyze the following weather data for any severe, unusual, or concerning conditions:

Current Weather Data:
{weather_data}

Active Weather Alerts (if any):
{weather_alerts}

Please evaluate and report on:

1. IMMEDIATE HAZARDS: Identify any conditions requiring immediate action
   - Extreme temperatures (below 0°F or above 100°F)
   - High wind speeds (above 40 mph)
   - Severe storms or tornado warnings
   - Flooding or flash flood risks
   - Ice, snow, or freezing rain

2. HEALTH & SAFETY CONCERNS:
   - Heat index or wind chill advisories
   - Air quality issues (smoke, haze, pollution)
   - Visibility problems affecting travel
   - Conditions affecting vulnerable populations

3. TRAVEL IMPACTS:
   - Driving conditions and visibility
   - Flight delay potential
   - Marine/boating advisories

4. RECOMMENDED ACTIONS:
   - Specific safety measures to take
   - Activities to avoid
   - Preparations needed

Severity Level: Classify overall severity as one of:
- SEVERE: Immediate danger to life or property
- MODERATE: Significant impacts requiring caution
- MINOR: Notable but manageable conditions
- NORMAL: No concerning conditions

Format the response clearly with sections for each concern identified.
Be direct and actionable in recommendations."""

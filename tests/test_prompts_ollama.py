#!/usr/bin/env python3
"""Test weather prompts with Ollama's gpt-oss:20b model."""

import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path
import yaml
from datetime import datetime

# Add parent directory to path to import prompt loader
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_prompt(prompt_name: str) -> tuple[str, dict | None]:
    """Load a prompt and its schema from the prompts directory."""
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{prompt_name}.yaml"
    schema_path = Path(__file__).parent.parent / "prompts" / f"{prompt_name}.json"

    with open(prompt_path, "r") as f:
        prompt_data = yaml.safe_load(f)

    schema = None
    if schema_path.exists():
        with open(schema_path, "r") as f:
            schema = json.load(f)

    return prompt_data["prompt"], schema


def inject_schema(prompt_text: str, schema: dict | None) -> str:
    """Inject JSON schema into prompt if placeholder exists."""
    if "{output_schema}" in prompt_text and schema:
        minified_schema = json.dumps(schema, separators=(",", ":"))
        prompt_text = prompt_text.replace("{output_schema}", minified_schema)
    return prompt_text


def call_ollama(prompt: str, model: str = "gpt-oss:20b") -> str:
    """Call Ollama API with the given prompt."""
    url = "http://localhost:11434/api/generate"

    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            return result.get("response", "No response received")
    except urllib.error.URLError as e:
        return f"Error calling Ollama: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


# Mock weather data (based on actual API responses shown earlier)
MOCK_WEATHER_DATA = {
    "Seattle": {
        "location": "Seattle, WA",
        "temperature": "55.4°F (13.0°C)",
        "conditions": "Smoke",
        "forecast": "Partly sunny. High near 64, with temperatures falling to around 62 in the afternoon. North wind around 5 mph.",
        "humidity": "82.0%",
        "wind": "0.0 mph from 0°",
        "timestamp": "2025-09-25T15:00:00+00:00",
        "source": "Weather.gov"
    },
    "Brownwood": {
        "location": "Brownwood, TX",
        "temperature": "69.8°F (21.0°C)",
        "conditions": "Haze",
        "forecast": "Sunny, with a high near 86. North wind 5 to 10 mph.",
        "humidity": "77.9%",
        "wind": "5.8 mph from 330°",
        "timestamp": "2025-09-25T15:00:00+00:00",
        "source": "Weather.gov"
    },
    "Phoenix": {
        "location": "Phoenix, AZ",
        "temperature": "105.2°F (40.7°C)",
        "conditions": "Clear",
        "forecast": "Sunny and hot, with a high near 108. Southwest wind around 10 mph.",
        "humidity": "15.0%",
        "wind": "10.2 mph from 220°",
        "timestamp": "2025-09-25T15:00:00+00:00",
        "source": "Weather.gov"
    }
}

MOCK_WEATHER_ALERTS = {
    "timestamp": "2025-09-25T15:00:00+00:00",
    "count": 3,
    "alerts": [
        {
            "headline": "Heat Advisory until 8:00 PM MST",
            "severity": "Moderate",
            "urgency": "Expected",
            "areas": "Phoenix Metro Area, Maricopa County",
            "description": "Dangerously hot conditions with temperatures up to 108 degrees expected. Drink plenty of fluids, stay in air-conditioning..."
        },
        {
            "headline": "Air Quality Alert until 12:00 PM PST",
            "severity": "Minor",
            "urgency": "Expected",
            "areas": "Puget Sound Region",
            "description": "Smoke from wildfires causing unhealthy air quality. Sensitive groups should limit outdoor activities..."
        }
    ]
}


def test_weather_report():
    """Test the weather report prompt."""
    print("Testing weather_report prompt...")
    prompt_text, schema = load_prompt("weather_report")
    prompt_text = inject_schema(prompt_text, schema)

    # Fill in the variables
    prompt = prompt_text.replace("{weather_data}", json.dumps(MOCK_WEATHER_DATA["Seattle"], indent=2))
    prompt = prompt.replace("{output_format}", "detailed paragraph format")

    response = call_ollama(prompt)

    output_path = Path("tests/test_output/weather_report_test.txt")
    with open(output_path, "w") as f:
        f.write("WEATHER REPORT PROMPT TEST\n")
        f.write("=" * 60 + "\n\n")
        f.write("Input Weather Data:\n")
        f.write(json.dumps(MOCK_WEATHER_DATA["Seattle"], indent=2) + "\n\n")
        f.write("Generated Report:\n")
        f.write("-" * 40 + "\n")
        f.write(response + "\n")

    print(f"✓ Weather report test saved to {output_path}")
    return response


def test_severe_weather_alert():
    """Test the severe weather alert prompt."""
    print("Testing severe_weather_alert prompt...")
    prompt_text, schema = load_prompt("severe_weather_alert")

    # Use Phoenix data for heat advisory scenario
    prompt = prompt_text.replace("{weather_data}", json.dumps(MOCK_WEATHER_DATA["Phoenix"], indent=2))
    prompt = prompt.replace("{weather_alerts}", json.dumps(MOCK_WEATHER_ALERTS, indent=2))

    response = call_ollama(prompt)

    output_path = Path("tests/test_output/severe_weather_alert_test.txt")
    with open(output_path, "w") as f:
        f.write("SEVERE WEATHER ALERT PROMPT TEST\n")
        f.write("=" * 60 + "\n\n")
        f.write("Input Weather Data:\n")
        f.write(json.dumps(MOCK_WEATHER_DATA["Phoenix"], indent=2) + "\n\n")
        f.write("Input Alerts:\n")
        f.write(json.dumps(MOCK_WEATHER_ALERTS, indent=2) + "\n\n")
        f.write("Generated Alert Analysis:\n")
        f.write("-" * 40 + "\n")
        f.write(response + "\n")

    print(f"✓ Severe weather alert test saved to {output_path}")
    return response


def test_weather_comparison():
    """Test the weather comparison prompt."""
    print("Testing weather_comparison prompt...")
    prompt_text, schema = load_prompt("weather_comparison")

    # Compare three locations
    locations_data = {
        "locations": [
            MOCK_WEATHER_DATA["Seattle"],
            MOCK_WEATHER_DATA["Brownwood"],
            MOCK_WEATHER_DATA["Phoenix"]
        ]
    }

    prompt = prompt_text.replace("{locations_data}", json.dumps(locations_data, indent=2))
    prompt = prompt.replace("{comparison_style}", "table format with recommendations")

    response = call_ollama(prompt)

    output_path = Path("tests/test_output/weather_comparison_test.txt")
    with open(output_path, "w") as f:
        f.write("WEATHER COMPARISON PROMPT TEST\n")
        f.write("=" * 60 + "\n\n")
        f.write("Input Location Data:\n")
        f.write(json.dumps(locations_data, indent=2) + "\n\n")
        f.write("Generated Comparison:\n")
        f.write("-" * 40 + "\n")
        f.write(response + "\n")

    print(f"✓ Weather comparison test saved to {output_path}")
    return response


def test_daily_forecast_brief():
    """Test the daily forecast brief prompt."""
    print("Testing daily_forecast_brief prompt...")
    prompt_text, schema = load_prompt("daily_forecast_brief")

    # Use Brownwood data with extended forecast info
    forecast_data = {
        "today": "Sunny, with a high near 86. North wind 5 to 10 mph.",
        "tonight": "Clear, with a low around 58. North wind around 5 mph becoming calm in the evening.",
        "tomorrow": "Sunny, with a high near 88. Calm wind becoming south around 5 mph in the afternoon.",
        "extended": "Warm and dry conditions expected through the weekend."
    }

    prompt = prompt_text.replace("{current_weather}", json.dumps(MOCK_WEATHER_DATA["Brownwood"], indent=2))
    prompt = prompt.replace("{forecast_data}", json.dumps(forecast_data, indent=2))
    prompt = prompt.replace("{target_audience}", "general public commuters")

    response = call_ollama(prompt)

    output_path = Path("tests/test_output/daily_forecast_brief_test.txt")
    with open(output_path, "w") as f:
        f.write("DAILY FORECAST BRIEF PROMPT TEST\n")
        f.write("=" * 60 + "\n\n")
        f.write("Current Weather:\n")
        f.write(json.dumps(MOCK_WEATHER_DATA["Brownwood"], indent=2) + "\n\n")
        f.write("Forecast Data:\n")
        f.write(json.dumps(forecast_data, indent=2) + "\n\n")
        f.write("Generated Brief:\n")
        f.write("-" * 40 + "\n")
        f.write(response + "\n")

    print(f"✓ Daily forecast brief test saved to {output_path}")
    return response


def main():
    """Run all prompt tests."""
    print("Starting Weather MCP Prompt Tests with Ollama gpt-oss:20b")
    print("=" * 60)

    # Check if Ollama is running
    test_prompt = "Say 'OK' if you can hear me."
    test_response = call_ollama(test_prompt)
    if "Error" in test_response:
        print(f"⚠️  Cannot connect to Ollama: {test_response}")
        print("Make sure Ollama is running: ollama serve")
        print("And the model is available: ollama pull gpt-oss:20b")
        return

    print("✓ Ollama connection successful\n")

    # Run all tests
    try:
        test_weather_report()
        print()

        test_severe_weather_alert()
        print()

        test_weather_comparison()
        print()

        test_daily_forecast_brief()
        print()

        print("=" * 60)
        print("✓ All prompt tests completed!")
        print(f"Results saved to: tests/test_output/")

        # Create a summary file
        summary_path = Path("tests/test_output/test_summary.txt")
        with open(summary_path, "w") as f:
            f.write("WEATHER MCP PROMPT TEST SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Test Date: {datetime.now().isoformat()}\n")
            f.write(f"Model Used: gpt-oss:20b (Ollama)\n\n")
            f.write("Tests Completed:\n")
            f.write("1. ✓ weather_report - Generate professional weather report\n")
            f.write("2. ✓ severe_weather_alert - Analyze severe conditions\n")
            f.write("3. ✓ weather_comparison - Compare multiple locations\n")
            f.write("4. ✓ daily_forecast_brief - Create daily briefing\n\n")
            f.write("All test outputs saved in tests/test_output/\n")

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
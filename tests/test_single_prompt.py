#!/usr/bin/env python3
"""Quick test of a single prompt with Ollama after linting fixes."""

import json
import sys
import urllib.request
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_weather_report():
    """Test the weather report prompt with Ollama."""

    # Load prompt
    prompt_path = Path(__file__).parent.parent / "prompts" / "weather_report.yaml"
    schema_path = Path(__file__).parent.parent / "prompts" / "weather_report.json"

    with open(prompt_path, "r") as f:
        prompt_data = yaml.safe_load(f)

    prompt_text = prompt_data["prompt"]

    # Inject schema if present
    if "{output_schema}" in prompt_text and schema_path.exists():
        with open(schema_path, "r") as f:
            schema = json.load(f)
        minified = json.dumps(schema, separators=(",", ":"))
        prompt_text = prompt_text.replace("{output_schema}", minified)

    # Fill in test data
    test_weather = {
        "location": "Test City, TC",
        "temperature": "72.0°F (22.2°C)",
        "conditions": "Clear",
        "forecast": "Sunny all day",
        "humidity": "50%",
        "wind": "5 mph from N"
    }

    prompt = prompt_text.replace("{weather_data}", json.dumps(test_weather, indent=2))
    prompt = prompt.replace("{output_format}", "brief JSON format")

    # Call Ollama
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "gpt-oss:20b",
        "prompt": prompt[:500] + "... [truncated for speed] Generate a brief test response.",
        "stream": False,
        "options": {"temperature": 0.5, "max_tokens": 100}
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            print("✓ Ollama responded successfully")
            print(f"Response preview: {result.get('response', '')[:100]}...")
            return True
    except Exception as e:
        print(f"✗ Ollama error: {e}")
        return False

if __name__ == "__main__":
    success = test_weather_report()
    sys.exit(0 if success else 1)
# Weather MCP Server

A FastMCP 2.x server providing AI systems with comprehensive access to US weather data, including current conditions, forecasts, and historical observations from authoritative sources.

## Features

- **Current Weather**: Real-time conditions and forecasts from Weather.gov (National Weather Service)
- **Historical Data**: Daily, monthly, and yearly observations from NOAA Climate Data Online
- **Multiple Detail Levels**: Brief, standard, or detailed responses for current conditions
- **Intelligent Geocoding**: Location text or coordinates via OpenStreetMap Nominatim
- **AI-Ready Prompts**: Weather reports, forecasts, comparisons, and severe weather analysis
- **Data Attribution**: Built-in citation resources for compliance

## Quick Start

### Prerequisites

- Python 3.11+
- NOAA CDO API token (free) for historical data: [Request token](https://www.ncdc.noaa.gov/cdo-web/token)

### Local Development

```bash
# Install dependencies
make install

# Set NOAA token for historical queries (optional)
export NOAA_CDO_TOKEN=your_token_here

# Run server locally
make run-local

# Test with cmcp (in another terminal)
cmcp ".venv/bin/python -m src.main" tools/list
```

### Deploy to OpenShift

```bash
# One-command deployment
make deploy

# Or deploy to specific project
make deploy PROJECT=my-project
```

## Tools

### `weather_current`

Get current weather conditions and forecast for US locations.

**Parameters:**
- `location` (string): City and state (e.g., "Seattle, WA") - OR -
- `latitude`/`longitude` (float): Coordinates
- `detail_level`: `brief` | `standard` | `detailed`

**Example:**
```json
{
  "location": "Denver, CO",
  "detail_level": "standard"
}
```

### `weather_historical`

Query historical weather observations from NOAA's GHCND network.

**Parameters:**
- `location` (string): City and state format
- `start_date` / `end_date` (string): YYYY-MM-DD format
- `measurements` (list): `TMAX`, `TMIN`, `TAVG`, `PRCP`, `SNOW`, `SNWD`
- `granularity`: `daily` (max 1 year) | `monthly` | `yearly`
- `include_observations` (bool): Include detailed observation array

**Example:**
```json
{
  "location": "Chicago, IL",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "measurements": ["TMAX", "TMIN", "PRCP"],
  "granularity": "monthly"
}
```

**Requires:** `NOAA_CDO_TOKEN` environment variable

## Resources

| URI | Description |
|-----|-------------|
| `info://data-sources` | Metadata about all weather data sources, reliability, and limitations |
| `citations://weather-api` | Weather.gov attribution and terms |
| `citations://geocode-api` | OpenStreetMap Nominatim attribution |
| `citations://all` | Combined citations for all APIs |

## Prompts

| Prompt | Description |
|--------|-------------|
| `weather_report` | Professional weather reports (narrative, structured, brief) |
| `daily_forecast_brief` | Comprehensive daily briefings with activity recommendations |
| `weather_comparison` | Compare conditions across multiple locations |
| `severe_weather_alert` | Analyze conditions for hazards and safety concerns |

## Data Sources

### Weather.gov (National Weather Service)
- **Coverage**: United States and territories
- **Data**: Current observations, forecasts, alerts
- **Updates**: Hourly (observations), 2-4x daily (forecasts)
- **Authentication**: None required (public domain)

### NOAA Climate Data Online
- **Coverage**: US and territories, extensive historical records
- **Data**: Daily observations (temperature, precipitation, snow)
- **Authentication**: Free API token required
- **Rate Limits**: 5 req/sec, 10,000 req/day

### OpenStreetMap Nominatim
- **Coverage**: Worldwide geocoding
- **Rate Limits**: 1 request/second
- **License**: ODbL (attribution required for displayed locations)

## Environment Variables

### Required for Historical Data
- `NOAA_CDO_TOKEN` - NOAA Climate Data Online API token

### Transport Configuration
- `MCP_TRANSPORT` - `stdio` (default) or `http`
- `MCP_HOT_RELOAD` - Enable hot-reload for development
- `MCP_HTTP_HOST` - HTTP server host (default: `0.0.0.0`)
- `MCP_HTTP_PORT` - HTTP server port (default: `8080`)
- `MCP_HTTP_PATH` - HTTP endpoint path (default: `/mcp/`)

### Optional Authentication
- `MCP_AUTH_JWT_SECRET` - JWT secret for symmetric signing
- `MCP_AUTH_JWT_PUBLIC_KEY` - JWT public key for asymmetric
- `MCP_REQUIRED_SCOPES` - Comma-separated required scopes

## Project Structure

```
├── src/
│   ├── core/           # Server, loaders, authentication
│   ├── tools/          # weather_current, weather_historical
│   ├── resources/      # data_sources, api_citations
│   └── prompts/        # Prompt implementations
├── prompts/            # YAML prompt definitions
├── tests/              # Test suite
├── Containerfile       # Container definition (Red Hat UBI)
├── openshift.yaml      # OpenShift manifests
└── Makefile            # Common tasks
```

## Testing

```bash
# Run unit tests
make test

# Run with coverage
.venv/bin/pytest tests/ --cov=src --cov-report=html

# Test deployed server with MCP Inspector
npx @modelcontextprotocol/inspector https://<route-url>/mcp/
```

## Available Commands

```bash
make help         # Show all available commands
make install      # Install dependencies
make run-local    # Run locally with STDIO
make test         # Run test suite
make test-local   # Test with cmcp
make deploy       # Deploy to OpenShift
make clean        # Clean up OpenShift deployment
```

## Limitations

- **US Only**: Weather.gov data covers United States and territories only
- **Historical Token**: NOAA CDO token required for historical queries
- **Rate Limits**: Respect API rate limits (especially Nominatim: 1/sec)
- **Data Lag**: Historical data may have 1-2 day delay from NOAA

## License

MIT License - see [LICENSE](LICENSE) for details.

## Attribution

This server aggregates data from public sources. When displaying weather information to end users, include appropriate attribution per the `citations://` resources.

# None Value Handling Fix

## Problem
The MCP server was rejecting prompt arguments when tool responses contained `None` (null) values in dictionaries. Specifically:
- The `WeatherData` model has an optional `coordinates` field that defaults to `None`
- When tools returned this data, FastMCP serialized it as `{"coordinates": null, ...}`
- Prompts with `dict[str, str]` signatures rejected the None value, causing errors

## Solution
Implemented a three-part defense-in-depth strategy:

### Part 1: Configure Models to Exclude None During Serialization
**Files Modified:**
- `src/tools/models.py` - Added `to_prompt_dict()` method to `WeatherData` and `GeocodeData` classes
- `src/tools/get_weather.py` - Changed return type from `WeatherData` to `dict`, using `to_prompt_dict()`
- `src/tools/get_weather_from_coordinates.py` - Same changes as above
- `src/tools/geocode_location.py` - Changed return type from `GeocodeData` to `dict`, using `to_prompt_dict()`

**How it works:**
```python
class WeatherData(BaseModel):
    # ... fields ...
    coordinates: Optional[Coordinates] = Field(default=None, ...)

    def to_prompt_dict(self) -> dict:
        """Serialize excluding None values for MCP prompts."""
        return self.model_dump(exclude_none=True, mode='json')
```

Tools now return clean dictionaries without None values:
```python
weather_obj = WeatherData(**weather_data)
return weather_obj.to_prompt_dict()  # No "coordinates": null
```

### Part 2: Update Prompt Signatures for Flexibility
**Files Modified:**
- `src/prompts/weather_prompts.py` - Updated all prompts to accept `dict[str, str | None]`

**Changes:**
- `weather_report()`: Now accepts `dict[str, str | None]`
- `daily_forecast_brief()`: Updated both `current_weather` and `forecast_data` parameters
- `weather_comparison()`: Updated `locations_data` parameter
- `severe_weather_alert()`: Updated `weather_data` parameter

This provides defense-in-depth: even if None values somehow get through Part 1, prompts can still accept them gracefully.

### Part 3: Utility Functions for Future Use
**Files Created:**
- `src/tools/serializers.py` - Reusable serialization utilities

**Functions:**
- `serialize_for_prompt(model)`: Accepts any Pydantic model, returns dict without None values
- `serialize_model_dict(data)`: Filters None values from plain dictionaries

These utilities can be used by future tools or when working with external data sources.

## Testing
Created comprehensive test suite in `tests/test_serializers.py`:
- ✅ Test that `to_prompt_dict()` excludes None values
- ✅ Test that `to_prompt_dict()` includes non-None optional fields
- ✅ Test utility functions work correctly
- ✅ Test edge cases (empty dicts, all-None dicts)
- ✅ Verify default `model_dump()` still includes None (for comparison)

**Test Results:**
```
tests/test_serializers.py::test_weather_data_to_prompt_dict_excludes_none PASSED
tests/test_serializers.py::test_weather_data_to_prompt_dict_includes_coordinates PASSED
tests/test_serializers.py::test_geocode_data_to_prompt_dict PASSED
tests/test_serializers.py::test_serialize_for_prompt_excludes_none PASSED
tests/test_serializers.py::test_serialize_model_dict_excludes_none PASSED
tests/test_serializers.py::test_serialize_model_dict_empty_dict PASSED
tests/test_serializers.py::test_serialize_model_dict_all_none PASSED
tests/test_serializers.py::test_weather_data_model_dump_default_includes_none PASSED
```

## Impact
**Before:**
```json
{
  "location": "Austin, TX",
  "temperature": "66.9°F",
  "coordinates": null  // ❌ Causes MCP prompt validation error
}
```

**After:**
```json
{
  "location": "Austin, TX",
  "temperature": "66.9°F"
  // ✅ No null values, prompt validation succeeds
}
```

## Backward Compatibility
✅ All changes are backward compatible:
- Tools still validate data using Pydantic models internally
- External API contracts unchanged (tools still accept same parameters)
- Optional fields still work correctly when values are present
- Other tools and resources unaffected

## Next Steps
The agent should now be able to call the `weather_report` prompt with weather data from `get_weather` without encountering null value errors.

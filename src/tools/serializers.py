"""Serialization utilities for MCP tool responses."""

from typing import Any, Dict
from pydantic import BaseModel


def serialize_for_prompt(model: BaseModel) -> Dict[str, Any]:
    """Serialize a Pydantic model for use in MCP prompts.

    This function ensures that:
    - None/null values are excluded from the output
    - Data is in JSON-serializable format
    - The result is compatible with prompt parameter types

    Args:
        model: Pydantic model instance to serialize

    Returns:
        Dictionary with None values excluded, suitable for prompt parameters

    Example:
        >>> weather = WeatherData(location="Austin", temperature="70°F", coordinates=None)
        >>> serialize_for_prompt(weather)
        {"location": "Austin", "temperature": "70°F"}
    """
    return model.model_dump(exclude_none=True, mode='json')


def serialize_model_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Filter None values from a dictionary.

    Useful when working with dictionaries that may contain None values
    that need to be excluded before passing to prompts.

    Args:
        data: Dictionary that may contain None values

    Returns:
        Dictionary with None values removed

    Example:
        >>> serialize_model_dict({"a": 1, "b": None, "c": "test"})
        {"a": 1, "c": "test"}
    """
    return {k: v for k, v in data.items() if v is not None}

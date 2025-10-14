"""Final validation test with all features"""

from pydantic import Field
from fastmcp.prompts.prompt import Message, PromptMessage, PromptResult, TextContent
from fastmcp import Context
from core.app import mcp


@mcp.prompt(    name="final_validation",    title="Final Validation Test",    description="Final validation test with all features",    tags={"testing", "validation", "final"},    meta={'version': '1.0', 'status': 'testing'},)
async def test_final_validation(
    ctx: Context,
) -> PromptMessage:
    """Final validation test with all features

    Args:
        ctx: FastMCP Context object for accessing request metadata
    Returns:
        Formatted prompt for LLM interaction
    """
    content = f"""Analyze and process the following:

# TODO: Add specific prompt instructions"""

    return PromptMessage(
        role="user",
        content=TextContent(type="text", text=content)
    )


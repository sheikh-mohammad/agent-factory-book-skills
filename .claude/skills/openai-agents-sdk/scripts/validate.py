"""
Validate Script - Validate Agent Configuration

Checks agent configuration for common issues before deployment.
"""

import sys
from typing import List, Tuple


class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def add_error(self, message: str):
        self.errors.append(f"❌ ERROR: {message}")

    def add_warning(self, message: str):
        self.warnings.append(f"⚠️  WARNING: {message}")

    def add_info(self, message: str):
        self.info.append(f"ℹ️  INFO: {message}")

    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def print_results(self):
        print("\n" + "="*60)
        print("VALIDATION RESULTS")
        print("="*60)

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.info:
            print("\nInfo:")
            for info in self.info:
                print(f"  {info}")

        print("\n" + "="*60)
        if self.is_valid():
            print("✓ Validation passed!")
        else:
            print("✗ Validation failed!")
        print("="*60 + "\n")


def validate_agent_config(agent_config: dict) -> ValidationResult:
    """Validate agent configuration."""
    result = ValidationResult()

    # Check required fields
    if not agent_config.get("name"):
        result.add_error("Agent name is required")
    else:
        name = agent_config["name"]
        if len(name) > 64:
            result.add_error(f"Agent name too long: {len(name)} chars (max 64)")
        result.add_info(f"Agent name: {name}")

    # Check instructions
    instructions = agent_config.get("instructions", "")
    if not instructions:
        result.add_warning("Agent has no instructions (system prompt)")
    else:
        word_count = len(instructions.split())
        if word_count > 500:
            result.add_warning(f"Instructions are long: {word_count} words (consider being more concise)")
        result.add_info(f"Instructions: {word_count} words")

    # Check model
    model = agent_config.get("model", "gpt-4o")
    valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
    if model not in valid_models:
        result.add_warning(f"Unknown model: {model}")
    result.add_info(f"Model: {model}")

    # Check model settings
    model_settings = agent_config.get("model_settings", {})
    if model_settings:
        temp = model_settings.get("temperature")
        if temp is not None:
            if temp < 0 or temp > 1:
                result.add_error(f"Invalid temperature: {temp} (must be 0-1)")
            result.add_info(f"Temperature: {temp}")

        max_tokens = model_settings.get("max_tokens")
        if max_tokens is not None:
            if max_tokens < 1:
                result.add_error(f"Invalid max_tokens: {max_tokens}")
            elif max_tokens > 4096:
                result.add_warning(f"High max_tokens: {max_tokens} (may be expensive)")
            result.add_info(f"Max tokens: {max_tokens}")

    # Check tools
    tools = agent_config.get("tools", [])
    if tools:
        result.add_info(f"Tools: {len(tools)} configured")
        if len(tools) > 20:
            result.add_warning(f"Many tools: {len(tools)} (may confuse agent)")

    # Check handoffs
    handoffs = agent_config.get("handoffs", [])
    if handoffs:
        result.add_info(f"Handoffs: {len(handoffs)} agents")

    return result


def validate_tool_config(tool_config: dict) -> ValidationResult:
    """Validate tool configuration."""
    result = ValidationResult()

    # Check tool name
    if not tool_config.get("name"):
        result.add_error("Tool name is required")
    else:
        result.add_info(f"Tool name: {tool_config['name']}")

    # Check description
    description = tool_config.get("description", "")
    if not description:
        result.add_error("Tool description is required (LLM needs this)")
    else:
        word_count = len(description.split())
        if word_count < 5:
            result.add_warning("Tool description is very short (be more descriptive)")
        result.add_info(f"Description: {word_count} words")

    # Check parameters
    params = tool_config.get("parameters", {})
    if params:
        result.add_info(f"Parameters: {len(params)}")
        if len(params) > 10:
            result.add_warning(f"Many parameters: {len(params)} (consider simplifying)")

    # Check timeout
    timeout = tool_config.get("timeout")
    if timeout:
        if timeout > 30:
            result.add_warning(f"Long timeout: {timeout}s (may block agent)")
        result.add_info(f"Timeout: {timeout}s")

    return result


def main():
    print("\n" + "="*60)
    print("OPENAI AGENTS SDK - CONFIGURATION VALIDATOR")
    print("="*60)

    # Example agent configuration
    agent_config = {
        "name": "Example Agent",
        "instructions": "You are a helpful assistant.",
        "model": "gpt-4o-mini",
        "model_settings": {
            "temperature": 0.7,
            "max_tokens": 1000,
        },
        "tools": ["tool1", "tool2"],
    }

    # Example tool configuration
    tool_config = {
        "name": "search_database",
        "description": "Search the database for matching records",
        "parameters": {"query": "str", "limit": "int"},
        "timeout": 10.0,
    }

    # Validate agent
    print("\nValidating Agent Configuration...")
    agent_result = validate_agent_config(agent_config)
    agent_result.print_results()

    # Validate tool
    print("\nValidating Tool Configuration...")
    tool_result = validate_tool_config(tool_config)
    tool_result.print_results()

    # Overall result
    if agent_result.is_valid() and tool_result.is_valid():
        print("✓ All validations passed!")
        sys.exit(0)
    else:
        print("✗ Some validations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

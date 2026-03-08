"""
Test Tools Script - Test Custom Tools in Isolation

Tests function tools independently before using them with agents.
"""

import asyncio
import sys
from typing import Callable


class ToolTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name: str, tool: Callable, *args, **kwargs):
        """Test a tool with given arguments."""
        print(f"\nTesting: {name}")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")

        try:
            # Check if tool is async
            if asyncio.iscoroutinefunction(tool):
                result = asyncio.run(tool(*args, **kwargs))
            else:
                result = tool(*args, **kwargs)

            print(f"✓ Success")
            print(f"Result: {result}")
            self.passed += 1
            self.tests.append({"name": name, "status": "passed", "result": result})
            return result

        except Exception as e:
            print(f"✗ Failed")
            print(f"Error: {type(e).__name__}: {e}")
            self.failed += 1
            self.tests.append({"name": name, "status": "failed", "error": str(e)})
            return None

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print("="*60)

        if self.failed == 0:
            print("✓ All tests passed!")
            return 0
        else:
            print("✗ Some tests failed!")
            return 1


def example_sync_tool(text: str) -> str:
    """Example synchronous tool."""
    return f"Processed: {text}"


async def example_async_tool(delay: float) -> str:
    """Example asynchronous tool."""
    await asyncio.sleep(delay)
    return f"Completed after {delay}s"


def example_tool_with_validation(value: int) -> str:
    """Example tool with input validation."""
    if value < 0:
        raise ValueError("Value must be positive")
    return f"Result: {value * 2}"


def main():
    print("\n" + "="*60)
    print("OPENAI AGENTS SDK - TOOL TESTER")
    print("="*60)

    tester = ToolTester()

    # Test sync tool
    tester.test("Sync Tool - Valid Input", example_sync_tool, "hello")

    # Test async tool
    tester.test("Async Tool - Valid Input", example_async_tool, 0.1)

    # Test validation - valid
    tester.test("Validation Tool - Valid Input", example_tool_with_validation, 5)

    # Test validation - invalid
    tester.test("Validation Tool - Invalid Input", example_tool_with_validation, -1)

    # Print summary
    exit_code = tester.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

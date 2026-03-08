"""
Setup Script - Initialize New Agent Project

Creates a new agent project with boilerplate code and configuration.
"""

import os
import sys
from pathlib import Path


TEMPLATE_MAIN = '''"""
{project_name} - OpenAI Agent

TODO: Add project description
"""

import asyncio
import os
from dotenv import load_dotenv
from agents import Agent, Runner

# Load environment variables
load_dotenv()


async def main():
    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable required")

    # Create agent
    agent = Agent(
        name="{agent_name}",
        instructions="You are a helpful assistant.",
        model="gpt-4o-mini",
    )

    # Run agent
    result = await Runner.run(agent, "Hello! What can you help me with?")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
'''

TEMPLATE_ENV = '''# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here

# Application Configuration
LOG_LEVEL=INFO
MAX_TURNS=10
'''

TEMPLATE_REQUIREMENTS = '''# OpenAI Agents SDK
openai-agents-sdk

# Environment management
python-dotenv

# Optional: Web framework
# fastapi
# uvicorn

# Optional: Database
# asyncpg
# sqlalchemy

# Optional: Monitoring
# prometheus-client
# sentry-sdk
'''

TEMPLATE_GITIGNORE = '''.env
.env.local
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.vscode/
.idea/
*.log
'''


def create_project(project_name: str, directory: str = "."):
    """Create a new agent project."""
    project_path = Path(directory) / project_name

    # Create directory structure
    directories = [
        project_path,
        project_path / "tools",
        project_path / "agents",
        project_path / "tests",
    ]

    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {dir_path}")

    # Create main.py
    main_file = project_path / "main.py"
    agent_name = project_name.replace("-", " ").replace("_", " ").title()
    main_file.write_text(TEMPLATE_MAIN.format(
        project_name=project_name,
        agent_name=agent_name
    ))
    print(f"Created: {main_file}")

    # Create .env.example
    env_file = project_path / ".env.example"
    env_file.write_text(TEMPLATE_ENV)
    print(f"Created: {env_file}")

    # Create requirements.txt
    req_file = project_path / "requirements.txt"
    req_file.write_text(TEMPLATE_REQUIREMENTS)
    print(f"Created: {req_file}")

    # Create .gitignore
    gitignore_file = project_path / ".gitignore"
    gitignore_file.write_text(TEMPLATE_GITIGNORE)
    print(f"Created: {gitignore_file}")

    # Create empty __init__.py files
    for subdir in ["tools", "agents"]:
        init_file = project_path / subdir / "__init__.py"
        init_file.write_text("")
        print(f"Created: {init_file}")

    print(f"\n✓ Project '{project_name}' created successfully!")
    print(f"\nNext steps:")
    print(f"1. cd {project_name}")
    print(f"2. cp .env.example .env")
    print(f"3. Edit .env and add your OPENAI_API_KEY")
    print(f"4. pip install -r requirements.txt")
    print(f"5. python main.py")


def main():
    if len(sys.argv) < 2:
        print("Usage: python setup.py <project_name> [directory]")
        print("\nExample:")
        print("  python setup.py my-agent-project")
        print("  python setup.py my-agent-project ./projects")
        sys.exit(1)

    project_name = sys.argv[1]
    directory = sys.argv[2] if len(sys.argv) > 2 else "."

    create_project(project_name, directory)


if __name__ == "__main__":
    main()

"""
Multi-Agent System Template

Demonstrates handoffs between specialized agents.
"""

import asyncio
from agents import Agent, Runner
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


async def main():
    # Create specialized agents
    billing_agent = Agent(
        name="Billing Specialist",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You handle billing inquiries, payment issues, and subscription questions.
        Be precise about amounts and dates. Always verify account details.""",
        handoff_description="Handles billing, payments, refunds, and subscriptions",
    )

    technical_agent = Agent(
        name="Technical Support",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You provide technical support for product issues.
        Ask clarifying questions and guide users through troubleshooting.""",
        handoff_description="Handles technical issues, bugs, and troubleshooting",
    )

    # Create triage agent that routes to specialists
    triage_agent = Agent(
        name="Support Triage",
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You are the first point of contact for customer support.
        Determine the nature of the request and route to the appropriate specialist:
        - Billing/payment questions → Billing Specialist
        - Technical issues → Technical Support
        - General questions → Answer directly
        Be friendly and professional.""",
        handoffs=[billing_agent, technical_agent],
    )

    # Test queries
    queries = [
        "I have a question about my last invoice",
        "My app keeps crashing when I try to login",
        "What are your business hours?",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        result = await Runner.run(triage_agent, query)

        print(f"Handled by: {result.last_agent.name}")
        print(f"Response: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())

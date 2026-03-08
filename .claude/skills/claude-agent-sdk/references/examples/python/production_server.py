# Production FastAPI Server Example
# Demonstrates production-ready agent server with error handling, monitoring, and security

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from claude_agent_sdk import query, ClaudeAgentOptions
from datetime import datetime
import asyncio

app = FastAPI()

# Metrics tracking
metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_cost": 0.0
}

class AgentRequest(BaseModel):
    prompt: str
    user_id: str

class AgentResponse(BaseModel):
    result: str
    metadata: dict

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "metrics": metrics
    }

# Agent endpoint
@app.post("/agent", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    metrics["total_requests"] += 1
    start_time = datetime.now()
    result = []

    # Security: Block dangerous operations
    async def can_use_tool_hook(tool_name: str, tool_input: dict):
        # Log all tool usage
        print(f"[{request.user_id}] Tool: {tool_name}")

        # Block dangerous tools
        if tool_name in ["Bash", "Write", "Edit"]:
            return {"behavior": "block", "message": "Tool not allowed"}

        return {"behavior": "allow"}

    try:
        async for message in query(
            prompt=request.prompt,
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "WebSearch", "Grep"],
                disallowed_tools=["Bash", "Write", "Edit"],
                max_budget_usd=0.5,
                max_turns=30,
                can_use_tool=can_use_tool_hook
            )
        ):
            # Collect text responses
            if message.type == "text":
                result.append(message.text)

            # Handle final result
            if message.type == "result":
                duration = (datetime.now() - start_time).total_seconds() * 1000

                if message.subtype == "success":
                    metrics["successful_requests"] += 1
                    metrics["total_cost"] += message.total_cost_usd

                    # Log metrics
                    print(f"[{request.user_id}] Success - Cost: ${message.total_cost_usd:.4f}, Duration: {duration:.0f}ms")

                    return AgentResponse(
                        result="\n".join(result),
                        metadata={
                            "cost": message.total_cost_usd,
                            "turns": message.turn_count,
                            "duration": duration,
                            "session_id": message.session_id
                        }
                    )
                else:
                    metrics["failed_requests"] += 1
                    print(f"[{request.user_id}] Error: {message.subtype}")

                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error": message.subtype,
                            "message": get_error_message(message.subtype)
                        }
                    )

    except Exception as e:
        metrics["failed_requests"] += 1
        print(f"[{request.user_id}] Exception: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred"
            }
        )

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    return {
        **metrics,
        "average_cost": metrics["total_cost"] / metrics["successful_requests"] if metrics["successful_requests"] > 0 else 0,
        "success_rate": (metrics["successful_requests"] / metrics["total_requests"]) * 100 if metrics["total_requests"] > 0 else 0
    }

def get_error_message(subtype: str) -> str:
    """Helper function for error messages"""
    error_messages = {
        "error_max_turns": "Task exceeded maximum number of turns. Try simplifying the request.",
        "error_max_budget_usd": "Task exceeded budget limit. Try a simpler request.",
        "error_during_execution": "An error occurred during execution. Please try again."
    }
    return error_messages.get(subtype, "An unknown error occurred.")

if __name__ == "__main__":
    import uvicorn
    print("Agent server starting...")
    print("Health check: http://localhost:8000/health")
    print("Metrics: http://localhost:8000/metrics")
    uvicorn.run(app, host="0.0.0.0", port=8000)

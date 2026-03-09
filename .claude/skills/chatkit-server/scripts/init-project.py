#!/usr/bin/env python3
"""
ChatKit Project Initialization Script

Creates a new ChatKit project with the specified architecture pattern.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict

# Project templates by architecture pattern
TEMPLATES = {
    "simple": {
        "description": "Simple conversational agent without external data",
        "files": {
            "app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5170"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"status": "ChatKit backend running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.message}
            ]
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
            "requirements.txt": """fastapi==0.109.0
uvicorn[standard]==0.27.0
openai==1.12.0
pydantic==2.6.0
python-dotenv==1.0.0
""",
            "src/main.js": """const API_URL = 'http://localhost:8000';

async function sendMessage(message) {
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        return data.response || data.error;
    } catch (error) {
        console.error('Error:', error);
        return 'Error: Could not connect to server';
    }
}

// Simple UI
document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');

    async function handleSend() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage('user', message);
        messageInput.value = '';

        // Get response
        const response = await sendMessage(message);
        addMessage('assistant', response);
    }

    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.textContent = content;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    sendButton.addEventListener('click', handleSend);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });
});
""",
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatKit App</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; }
        #app { max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { margin-bottom: 20px; }
        #chat-box {
            border: 1px solid #ddd;
            border-radius: 8px;
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            margin-bottom: 20px;
            background: #f9f9f9;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 8px;
            max-width: 80%;
        }
        .message.user {
            background: #007bff;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .message.assistant {
            background: white;
            border: 1px solid #ddd;
        }
        #input-area { display: flex; gap: 10px; }
        #message-input {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        #send-button {
            padding: 12px 24px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }
        #send-button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div id="app">
        <h1>ChatKit App</h1>
        <div id="chat-box"></div>
        <div id="input-area">
            <input type="text" id="message-input" placeholder="Type your message...">
            <button id="send-button">Send</button>
        </div>
    </div>
    <script type="module" src="/src/main.js"></script>
</body>
</html>
""",
            "package.json": """{
  "name": "chatkit-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "backend": "uvicorn app.main:app --reload --port 8000",
    "frontend": "vite",
    "start": "concurrently \\"npm run backend\\" \\"npm run frontend\\""
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "concurrently": "^8.2.2"
  }
}
""",
            ".env.example": """OPENAI_API_KEY=sk-proj-your-key-here
VITE_CHATKIT_API_DOMAIN_KEY=your-domain-key
""",
            ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# Node
node_modules/
dist/
.vite/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
        }
    },
    "knowledge": {
        "description": "Knowledge assistant with vector store integration",
        "files": {
            # Similar structure but with vector store integration
            "app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5170"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VECTOR_STORE_ID = os.getenv("KNOWLEDGE_VECTOR_STORE_ID")

class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None

@app.get("/")
async def root():
    return {"status": "ChatKit Knowledge Assistant running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Create or reuse thread
        if not request.thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
        else:
            thread_id = request.thread_id

        # Add message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request.message
        )

        # Run with file search
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=os.getenv("ASSISTANT_ID"),
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [VECTOR_STORE_ID]
                }
            }
        )

        # Get response
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        latest = messages.data[0]

        # Extract citations
        citations = []
        for annotation in latest.content[0].text.annotations:
            if hasattr(annotation, 'file_citation'):
                citations.append({
                    "file_id": annotation.file_citation.file_id,
                    "quote": annotation.file_citation.quote
                })

        return {
            "response": latest.content[0].text.value,
            "thread_id": thread_id,
            "citations": citations
        }
    except Exception as e:
        return {"error": str(e)}
""",
            "requirements.txt": """fastapi==0.109.0
uvicorn[standard]==0.27.0
openai==1.12.0
pydantic==2.6.0
python-dotenv==1.0.0
""",
            ".env.example": """OPENAI_API_KEY=sk-proj-your-key-here
KNOWLEDGE_VECTOR_STORE_ID=vs_your-vector-store-id
ASSISTANT_ID=asst_your-assistant-id
VITE_CHATKIT_API_DOMAIN_KEY=your-domain-key
"""
        }
    },
    "tools": {
        "description": "Tool-augmented agent with custom functions",
        "files": {
            "app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5170"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define custom tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# Tool implementations
def get_current_time() -> dict:
    from datetime import datetime
    return {"time": datetime.now().isoformat()}

TOOL_FUNCTIONS = {
    "get_current_time": get_current_time
}

class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        if not request.thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
        else:
            thread_id = request.thread_id

        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request.message
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=os.getenv("ASSISTANT_ID"),
            tools=tools
        )

        # Handle tool calls
        while run.status in ["queued", "in_progress", "requires_action"]:
            if run.status == "requires_action":
                tool_outputs = []
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    result = TOOL_FUNCTIONS[function_name](**function_args)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        messages = client.beta.threads.messages.list(thread_id=thread_id)
        return {
            "response": messages.data[0].content[0].text.value,
            "thread_id": thread_id
        }
    except Exception as e:
        return {"error": str(e)}
""",
            "app/tools/__init__.py": """# Add your custom tools here
""",
            "requirements.txt": """fastapi==0.109.0
uvicorn[standard]==0.27.0
openai==1.12.0
pydantic==2.6.0
python-dotenv==1.0.0
"""
        }
    }
}


def create_project(name: str, pattern: str, output_dir: str = ".") -> None:
    """Create a new ChatKit project."""

    if pattern not in TEMPLATES:
        print(f"Error: Unknown pattern '{pattern}'")
        print(f"Available patterns: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    template = TEMPLATES[pattern]
    project_path = Path(output_dir) / name

    if project_path.exists():
        print(f"Error: Directory '{project_path}' already exists")
        sys.exit(1)

    print(f"Creating ChatKit project: {name}")
    print(f"Pattern: {pattern} - {template['description']}")
    print()

    # Create project directory
    project_path.mkdir(parents=True)

    # Create files from template
    for file_path, content in template["files"].items():
        full_path = project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        print(f"Created: {file_path}")

    print()
    print("Project created successfully!")
    print()
    print("Next steps:")
    print(f"  1. cd {name}")
    print("  2. cp .env.example .env")
    print("  3. Edit .env with your API keys")
    print("  4. npm install")
    print("  5. uv pip install -r requirements.txt")
    print("  6. npm start")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new ChatKit project"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Project name"
    )
    parser.add_argument(
        "--pattern",
        required=True,
        choices=list(TEMPLATES.keys()),
        help="Architecture pattern"
    )
    parser.add_argument(
        "--output",
        default=".",
        help="Output directory (default: current directory)"
    )

    args = parser.parse_args()
    create_project(args.name, args.pattern, args.output)


if __name__ == "__main__":
    main()

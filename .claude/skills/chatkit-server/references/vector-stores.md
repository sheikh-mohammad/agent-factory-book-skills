# Vector Stores Guide

Comprehensive guide for setting up and using vector stores in ChatKit applications.

---

## What are Vector Stores?

Vector stores enable semantic search over documents by:
1. Converting documents to embeddings (vectors)
2. Storing embeddings in a searchable index
3. Finding relevant documents based on query similarity

**Use Cases**: Knowledge bases, document search, RAG (Retrieval-Augmented Generation), citation-backed responses

---

## Creating Vector Stores

### Via OpenAI Platform (Recommended)

```bash
# 1. Go to https://platform.openai.com/storage/vector_stores
# 2. Click "Create vector store"
# 3. Name your vector store
# 4. Upload documents (PDF, DOCX, TXT, MD, etc.)
# 5. Copy the vector store ID (vs_...)
```

### Via API

```python
from openai import OpenAI

client = OpenAI()

# Create vector store
vector_store = client.beta.vector_stores.create(
    name="Company Knowledge Base"
)

print(f"Vector Store ID: {vector_store.id}")

# Upload files
file_paths = [
    "docs/policy.pdf",
    "docs/handbook.docx",
    "docs/procedures.md"
]

file_streams = [open(path, "rb") for path in file_paths]

# Batch upload
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id,
    files=file_streams
)

print(f"Uploaded {file_batch.file_counts.completed} files")

# Close file streams
for stream in file_streams:
    stream.close()
```

---

## Supported File Types

| Format | Extension | Max Size | Notes |
|--------|-----------|----------|-------|
| PDF | .pdf | 512 MB | Text extraction, OCR for images |
| Word | .docx | 512 MB | Formatting preserved |
| Text | .txt | 512 MB | Plain text |
| Markdown | .md | 512 MB | Formatting preserved |
| HTML | .html | 512 MB | Text extraction |
| JSON | .json | 512 MB | Structured data |
| CSV | .csv | 512 MB | Tabular data |

---

## Using Vector Stores in ChatKit

### Basic Integration

```python
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel
import os

app = FastAPI()
client = OpenAI()

VECTOR_STORE_ID = os.getenv("KNOWLEDGE_VECTOR_STORE_ID")

class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None

@app.post("/chat")
async def chat(request: ChatRequest):
    # Create or reuse thread
    if not request.thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id
    else:
        thread_id = request.thread_id

    # Add user message
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
    return {
        "response": messages.data[0].content[0].text.value,
        "thread_id": thread_id
    }
```

### With Citations

```python
def extract_citations(message):
    """Extract file citations from message."""
    citations = []
    text = message.content[0].text

    for annotation in text.annotations:
        if hasattr(annotation, 'file_citation'):
            citation = annotation.file_citation
            citations.append({
                "file_id": citation.file_id,
                "quote": citation.quote,
                "text": text.value[annotation.start_index:annotation.end_index]
            })

    return citations

@app.post("/chat")
async def chat(request: ChatRequest):
    # ... run assistant ...

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    latest = messages.data[0]

    return {
        "response": latest.content[0].text.value,
        "thread_id": thread_id,
        "citations": extract_citations(latest)
    }
```

---

## Multiple Vector Stores

### Use Case: Different Knowledge Domains

```python
# Environment variables
POLICY_VECTOR_STORE = os.getenv("POLICY_VECTOR_STORE_ID")
TECHNICAL_VECTOR_STORE = os.getenv("TECHNICAL_VECTOR_STORE_ID")
PRODUCT_VECTOR_STORE = os.getenv("PRODUCT_VECTOR_STORE_ID")

class ChatRequest(BaseModel):
    message: str
    domain: str  # "policy", "technical", "product"
    thread_id: str | None = None

@app.post("/chat")
async def chat(request: ChatRequest):
    # Select vector store based on domain
    vector_store_map = {
        "policy": POLICY_VECTOR_STORE,
        "technical": TECHNICAL_VECTOR_STORE,
        "product": PRODUCT_VECTOR_STORE
    }

    vector_store_id = vector_store_map.get(request.domain)
    if not vector_store_id:
        raise HTTPException(status_code=400, detail="Invalid domain")

    # ... create thread and message ...

    # Run with selected vector store
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=os.getenv("ASSISTANT_ID"),
        tools=[{"type": "file_search"}],
        tool_resources={
            "file_search": {
                "vector_store_ids": [vector_store_id]
            }
        }
    )

    # ... return response ...
```

### Use Case: Multi-Domain Search

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    # Search across multiple vector stores
    all_vector_stores = [
        POLICY_VECTOR_STORE,
        TECHNICAL_VECTOR_STORE,
        PRODUCT_VECTOR_STORE
    ]

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=os.getenv("ASSISTANT_ID"),
        tools=[{"type": "file_search"}],
        tool_resources={
            "file_search": {
                "vector_store_ids": all_vector_stores
            }
        }
    )

    # ... return response ...
```

---

## Managing Vector Stores

### List Vector Stores

```python
def list_vector_stores():
    """List all vector stores."""
    vector_stores = client.beta.vector_stores.list()
    for vs in vector_stores.data:
        print(f"ID: {vs.id}, Name: {vs.name}, Files: {vs.file_counts.total}")
```

### Update Vector Store

```python
def update_vector_store(vector_store_id: str, new_name: str):
    """Update vector store name."""
    vector_store = client.beta.vector_stores.update(
        vector_store_id=vector_store_id,
        name=new_name
    )
    return vector_store
```

### Add Files to Existing Vector Store

```python
def add_files_to_vector_store(vector_store_id: str, file_paths: list):
    """Add files to existing vector store."""
    file_streams = [open(path, "rb") for path in file_paths]

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store_id,
        files=file_streams
    )

    for stream in file_streams:
        stream.close()

    return file_batch
```

### Remove Files from Vector Store

```python
def remove_file_from_vector_store(vector_store_id: str, file_id: str):
    """Remove file from vector store."""
    client.beta.vector_stores.files.delete(
        vector_store_id=vector_store_id,
        file_id=file_id
    )
```

### Delete Vector Store

```python
def delete_vector_store(vector_store_id: str):
    """Delete vector store."""
    client.beta.vector_stores.delete(vector_store_id=vector_store_id)
```

---

## Best Practices

### Document Preparation

```python
def prepare_document(file_path: str) -> str:
    """Prepare document for vector store."""
    # 1. Clean text
    with open(file_path, 'r') as f:
        content = f.read()

    # 2. Remove excessive whitespace
    content = re.sub(r'\s+', ' ', content)

    # 3. Add metadata headers
    metadata = f"""
    Document: {os.path.basename(file_path)}
    Last Updated: {datetime.now().isoformat()}
    ---
    """

    # 4. Save prepared document
    prepared_path = f"prepared_{os.path.basename(file_path)}"
    with open(prepared_path, 'w') as f:
        f.write(metadata + content)

    return prepared_path
```

### Chunking Strategy

For large documents, consider pre-chunking:

```python
def chunk_document(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Split document into overlapping chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            if last_period > chunk_size * 0.8:  # At least 80% of chunk
                end = start + last_period + 1
                chunk = text[start:end]

        chunks.append(chunk)
        start = end - overlap  # Overlap for context

    return chunks
```

### Metadata Enrichment

```python
def add_metadata_to_document(file_path: str, metadata: dict) -> str:
    """Add metadata to document for better search."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Add metadata as frontmatter
    frontmatter = "---\n"
    for key, value in metadata.items():
        frontmatter += f"{key}: {value}\n"
    frontmatter += "---\n\n"

    enriched_path = f"enriched_{os.path.basename(file_path)}"
    with open(enriched_path, 'w') as f:
        f.write(frontmatter + content)

    return enriched_path

# Usage
metadata = {
    "department": "Engineering",
    "category": "Technical Documentation",
    "version": "2.0",
    "author": "Tech Team"
}
enriched_doc = add_metadata_to_document("api-docs.md", metadata)
```

---

## Performance Optimization

### Caching Search Results

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_vector_search(query_hash: str, vector_store_id: str):
    """Cache vector search results."""
    # This is called by the main function with hashed query
    pass

def search_with_cache(query: str, vector_store_id: str):
    """Search with caching."""
    query_hash = hashlib.md5(query.encode()).hexdigest()
    return cached_vector_search(query_hash, vector_store_id)
```

### Batch Processing

```python
async def process_multiple_queries(queries: list, vector_store_id: str):
    """Process multiple queries in parallel."""
    import asyncio

    async def process_single(query: str):
        # Process single query
        return await search_vector_store(query, vector_store_id)

    results = await asyncio.gather(*[process_single(q) for q in queries])
    return results
```

---

## Monitoring and Analytics

### Track Search Performance

```python
import time

def track_search_metrics(func):
    """Decorator to track search metrics."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        # Log metrics
        logger.info(f"Vector search completed in {duration:.2f}s")

        return result
    return wrapper

@track_search_metrics
def search_vector_store(query: str, vector_store_id: str):
    # ... search logic ...
    pass
```

### Monitor Vector Store Usage

```python
def get_vector_store_stats(vector_store_id: str):
    """Get vector store statistics."""
    vector_store = client.beta.vector_stores.retrieve(vector_store_id)

    return {
        "id": vector_store.id,
        "name": vector_store.name,
        "total_files": vector_store.file_counts.total,
        "completed_files": vector_store.file_counts.completed,
        "failed_files": vector_store.file_counts.failed,
        "in_progress_files": vector_store.file_counts.in_progress,
        "created_at": vector_store.created_at,
        "last_active_at": vector_store.last_active_at
    }
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Vector store not found" | Invalid ID or deleted | Verify ID, recreate if needed |
| "File upload failed" | Unsupported format or too large | Check format and size limits |
| "No results returned" | Documents not indexed yet | Wait for indexing to complete |
| "Poor search quality" | Documents lack context | Add metadata, improve chunking |
| "Slow search" | Too many documents | Split into multiple vector stores |

### Debug Vector Store Issues

```python
def debug_vector_store(vector_store_id: str):
    """Debug vector store issues."""
    try:
        vs = client.beta.vector_stores.retrieve(vector_store_id)
        print(f"Vector Store: {vs.name}")
        print(f"Status: {vs.status}")
        print(f"Files: {vs.file_counts.total}")

        # List files
        files = client.beta.vector_stores.files.list(vector_store_id)
        for file in files.data:
            print(f"  File: {file.id}, Status: {file.status}")

    except Exception as e:
        print(f"Error: {str(e)}")
```

---

## Vector Store Checklist

- [ ] Vector store created on OpenAI platform
- [ ] Documents uploaded and indexed
- [ ] Vector store ID stored in environment variables
- [ ] File search tool enabled in assistant
- [ ] Citations extraction implemented (if needed)
- [ ] Multiple vector stores configured (if needed)
- [ ] Document preparation workflow established
- [ ] Metadata enrichment implemented
- [ ] Search caching configured (for performance)
- [ ] Monitoring and analytics set up
- [ ] Backup strategy for documents
- [ ] Regular updates scheduled for knowledge base

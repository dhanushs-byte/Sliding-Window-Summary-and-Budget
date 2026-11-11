# Week 5 – Day 3: LLM Application Development

## Overview

This project focuses on building reliable LLM applications using context management techniques and FastAPI.

The assessment covers sliding window conversation management, automatic summarisation, token budgeting, FastAPI routes, Pydantic validation, and request tracking middleware.

## Technologies Used

- Python 3.14
- OpenRouter API
- OpenAI Python SDK
- FastAPI
- Uvicorn
- Pydantic
- Asyncio
- Tiktoken
- Python-dotenv
- JSON

## Project Structure

```text
week5_day3_context_api/
│
├── .env
├── .gitignore
├── requirements.txt
│
├── task1_context_management.py
├── task2_fastapi.py
│
├── conversations/
│   └── summary.json
│
└── README.md
```

# Task 1 – Sliding Window, Summary and Budget

## Objective

Implement context management techniques to control conversation history, reduce token usage, and preserve important information during long LLM conversations.

## 1. Sliding Window

Implemented a sliding window mechanism that maintains:

- System prompt.
- Most recent four conversation turns.
- Older conversation messages are removed from active history.

This helps reduce unnecessary token usage while retaining recent context.

## 2. Automatic Summarisation

Implemented automatic summarisation when conversation history exceeds 2,000 tokens.

The application:

1. Checks conversation history token count.
2. Identifies older conversation messages.
3. Sends older messages to the LLM for summarisation.
4. Preserves important details such as names and order IDs.
5. Stores the summary separately.
6. Retains the latest four conversation turns.

## 3. Token Budget

Configured the following token allocation:

| Component | Token Budget |
|---|---:|
| System Prompt | 500 |
| Conversation History | 3,000 |
| Context Summary | 2,000 |
| Model Output | 1,000 |
| **Total** | **6,500** |

The application checks token limits before every LLM API call.

## 4. Twenty-Turn Conversation

Executed a 20-turn conversation to demonstrate context management and automatic summarisation.

The application displays:

- History token count before processing.
- History token count after trimming.
- Summary token count.
- Token budget validation.

Example output format:

```text
TURN: 20

History before trimming: [actual count]

History exceeds 2000 tokens.
Starting summarisation...

Old history tokens: [actual count]
Summary tokens: [actual count]
Recent history tokens: [actual count]

History after trimming: [actual count]
```

## 5. Important Fact Preservation

Tested whether important information from early conversation turns survives summarisation.

Initial conversation:

```text
My name is Arun.
My important order ID is 9999.
```

Verification question:

```text
What is my name and what is my important order ID?
```

Expected response:

```text
Your name is Arun.
Your important order ID is 9999.
```

## Key Concepts

- Sliding window
- Conversation summarisation
- Token counting
- Token budget allocation
- Context management
- Important fact preservation

# Task 2 – FastAPI Routes and Pydantic Models

## Objective

Create REST API endpoints using FastAPI and validate incoming requests using Pydantic models.

## 1. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application status |
| GET | `/sessions/{session_id}` | Retrieve conversation session |
| POST | `/chat` | Submit a chat message |

## 2. Pydantic Request Model

Implemented `ChatRequest` with field validation.

```python
class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000
    )
```

Validation rules:

- Message cannot be empty.
- Minimum length is 1 character.
- Maximum length is 2,000 characters.

## 3. Pydantic Response Model

```python
class ChatResponse(BaseModel):
    session_id: str
    reply: str
```

This ensures that API responses follow a consistent structure.

## 4. model_validate() and model_dump()

### model_validate()

Validates incoming Python data against a Pydantic model.

```python
validated_request = ChatRequest.model_validate({
    "message": request.message
})
```

### model_dump()

Converts a validated Pydantic model into a Python dictionary.

```python
request_data = validated_request.model_dump()
```

These methods support data validation and structured data processing.

## 5. API Testing

Started the FastAPI application using:

```bash
uvicorn task2_fastapi:app --reload
```

Swagger documentation:

http://127.0.0.1:8000/docs

### GET /

Expected response:

```json
{
  "message": "LLM FastAPI Application is running",
  "docs": "/docs"
}
```

### POST /chat

Request:

```json
{
  "message": "Hello AI"
}
```

Expected response:

```json
{
  "session_id": "session_001",
  "reply": "AI received your message: Hello AI"
}
```

### GET /sessions/{session_id}

Retrieves stored messages for a session.

### Empty Message Validation – HTTP 422

Request:

```json
{
  "message": ""
}
```

Expected response:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "message"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```

The 422 response demonstrates automatic request validation by FastAPI and Pydantic.

# Bonus Challenge – Request ID Middleware

Implemented middleware to generate a unique UUID for each incoming API request.

```python
@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = str(uuid.uuid4())

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response
```

Example response header:

```text
X-Request-ID: generated-uuid
```

### Benefits

- Request tracking.
- Debugging API requests.
- Error investigation.
- Request identification.

# Installation and Execution

## Step 1 – Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2 – Configure Environment Variables

Create `.env`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
MODEL_NAME=openai/gpt-4o-mini
```

Never upload API keys or `.env` files to GitHub.

## Step 3 – Run Task 1

```bash
python task1_context_management.py
```

## Step 4 – Run Task 2

```bash
uvicorn task2_fastapi:app --reload
```

Open Swagger UI:

http://127.0.0.1:8000/docs

Test all available endpoints using the interactive documentation.

# Learning Outcomes

1. Implemented sliding window context management.
2. Used LLM summarisation to compress older conversation history.
3. Applied token budgets to control LLM API requests.
4. Preserved important information during summarisation.
5. Created REST API endpoints using FastAPI.
6. Implemented Pydantic request and response models.
7. Used `model_validate()` and `model_dump()`.
8. Tested API validation and HTTP 422 responses.
9. Implemented request ID middleware for API tracking.

# Conclusion

Successfully implemented context management techniques and FastAPI fundamentals for LLM application development.

This assessment provided practical experience in managing long conversations, controlling token usage, preserving important context, validating API requests, and building structured AI application endpoints.

---

**Week:** 5  
**Day:** 3  
**Module:** LLM Application Development  
**Tasks:** Context Management and FastAPI  
**Bonus:** X-Request-ID Middleware

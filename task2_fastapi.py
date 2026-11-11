
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Dict, List
import uuid

app = FastAPI(
    title="LLM Application API",
    description="FastAPI routes and Pydantic validation demo",
    version="1.0.0"
)


# -------------------------------
# 1. Pydantic Request Model
# -------------------------------

class ChatRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=2000,
        description="User message"
    )


# -------------------------------
# 2. Pydantic Response Model
# -------------------------------

class ChatResponse(BaseModel):

    session_id: str
    reply: str


# -------------------------------
# 3. In-memory session storage
# -------------------------------

sessions: Dict[str, List[dict]] = {}


# -------------------------------
# 4. Request ID Middleware
# -------------------------------

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):

    request_id = str(uuid.uuid4())

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -------------------------------
# 5. GET Session Route
# -------------------------------

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):

    if session_id not in sessions:

        return {
            "session_id": session_id,
            "messages": [],
            "message": "Session not found"
        }

    return {
        "session_id": session_id,
        "messages": sessions[session_id]
    }


# -------------------------------
# 6. POST Chat Route
# -------------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    # Demonstrate model_validate()
    validated_request = ChatRequest.model_validate({
        "message": request.message
    })

    # Demonstrate model_dump()
    request_data = validated_request.model_dump()

    message = request_data["message"]

    session_id = "session_001"

    if session_id not in sessions:
        sessions[session_id] = []

    sessions[session_id].append({
        "role": "user",
        "content": message
    })

    # Demo response
    reply = f"AI received your message: {message}"

    sessions[session_id].append({
        "role": "assistant",
        "content": reply
    })

    response = ChatResponse(
        session_id=session_id,
        reply=reply
    )

    return response


# -------------------------------
# 7. Root Route
# -------------------------------

@app.get("/")
async def home():

    return {
        "message": "LLM FastAPI Application is running",
        "docs": "/docs"
    }

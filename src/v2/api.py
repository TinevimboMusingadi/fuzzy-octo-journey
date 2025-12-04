"""FastAPI HTTP API for V2.0 pre-built forms.

Endpoints:
- POST /api/forms/start - Create a new form session
- POST /api/forms/answer - Submit an answer to the current question
- GET /api/forms/result/{session_id} - Get collected form data

Example usage:
    uvicorn src.v2.api:app --reload --port 8000
"""

import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.messages import HumanMessage

from src.v2.session import create_session

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Dynamic Intake Form Agent API",
    description="V2.0 HTTP API for pre-built form schemas",
    version="2.0.0",
)

# Enable CORS for web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (in production, use Redis/DB)
_sessions: Dict[str, Dict[str, Any]] = {}


# Request/Response Models
class StartFormRequest(BaseModel):
    form_id: str
    mode: str = "hybrid"


class StartFormResponse(BaseModel):
    session_id: str
    question: str
    is_complete: bool = False


class AnswerRequest(BaseModel):
    session_id: str
    message: str


class AnswerResponse(BaseModel):
    question: Optional[str] = None
    is_complete: bool
    collected_fields: Dict[str, Any] = {}


class FormResultResponse(BaseModel):
    session_id: str
    form_id: str
    collected_fields: Dict[str, Any]
    metadata: Dict[str, Any]


# API Endpoints
@app.post("/api/forms/start", response_model=StartFormResponse)
async def start_form(request: StartFormRequest) -> StartFormResponse:
    """Create a new form session and return the first question."""
    # Validate form_id
    from src.v2.forms_registry import get_form_schema
    
    schema = get_form_schema(request.form_id)
    if not schema:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown form_id: {request.form_id}. Available: employment_onboarding, rental_application, tax_1040_mvp, healthcare_intake"
        )
    
    # Validate mode
    if request.mode not in ["speed", "quality", "hybrid"]:
        raise HTTPException(
            status_code=400,
            detail="mode must be one of: speed, quality, hybrid"
        )
    
    # Create session
    session = create_session(form_id=request.form_id, mode=request.mode)
    graph = session["graph"]
    state = session["state"]
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Run graph to get first question
    config_run = {"configurable": {"thread_id": session_id}}
    
    # Stream until we get a question
    for _ in graph.stream(state, config_run):
        pass
    
    # Get current state and extract question
    current_state = graph.get_state(config_run)
    messages = current_state.values.get("messages", [])
    
    # Find last AI message (the question)
    question = ""
    for msg in reversed(messages):
        msg_type = getattr(msg, "type", None) or getattr(msg, "role", None) or msg.__dict__.get("type")
        if msg_type == "ai":
            question = getattr(msg, "content", "") or getattr(msg, "text", "")
            break
    
    # Store session
    _sessions[session_id] = {
        "graph": graph,
        "config_run": config_run,
        "form_id": request.form_id,
        "mode": request.mode,
        "created_at": datetime.now().isoformat(),
    }
    
    return StartFormResponse(
        session_id=session_id,
        question=question,
        is_complete=current_state.values.get("is_complete", False),
    )


@app.post("/api/forms/answer", response_model=AnswerResponse)
async def submit_answer(request: AnswerRequest) -> AnswerResponse:
    """Submit an answer and get the next question or completion status."""
    # Check session exists
    if request.session_id not in _sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {request.session_id} not found"
        )
    
    session_data = _sessions[request.session_id]
    graph = session_data["graph"]
    config_run = session_data["config_run"]
    
    # Add user message and resume graph
    graph.update_state(
        config_run,
        {"messages": [HumanMessage(content=request.message)]},
    )
    
    # Stream until next question or completion
    for _ in graph.stream(None, config_run):
        pass
    
    # Get updated state
    current_state = graph.get_state(config_run)
    values = current_state.values
    
    # Extract question from messages
    messages = values.get("messages", [])
    question = None
    for msg in reversed(messages):
        msg_type = getattr(msg, "type", None) or getattr(msg, "role", None) or msg.__dict__.get("type")
        if msg_type == "ai":
            question = getattr(msg, "content", "") or getattr(msg, "text", "")
            break
    
    is_complete = values.get("is_complete", False)
    collected_fields = values.get("collected_fields", {})
    
    return AnswerResponse(
        question=question,
        is_complete=is_complete,
        collected_fields=collected_fields,
    )


@app.get("/api/forms/result/{session_id}", response_model=FormResultResponse)
async def get_result(session_id: str) -> FormResultResponse:
    """Get the final collected form data for a completed session."""
    if session_id not in _sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    session_data = _sessions[session_id]
    graph = session_data["graph"]
    config_run = session_data["config_run"]
    
    # Get current state
    current_state = graph.get_state(config_run)
    values = current_state.values
    
    collected_fields = values.get("collected_fields", {})
    
    return FormResultResponse(
        session_id=session_id,
        form_id=session_data["form_id"],
        collected_fields=collected_fields,
        metadata={
            "mode": session_data["mode"],
            "created_at": session_data["created_at"],
            "is_complete": values.get("is_complete", False),
        },
    )


@app.get("/api/forms/list")
async def list_forms() -> Dict[str, Any]:
    """List available form IDs."""
    from src.v2.forms_registry import FORM_REGISTRY
    
    return {
        "forms": [
            {
                "id": form_id,
                "name": schema.get("name", form_id),
                "field_count": len(schema.get("fields", [])),
            }
            for form_id, schema in FORM_REGISTRY.items()
        ]
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API info."""
    return {
        "message": "Dynamic Intake Form Agent API v2.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


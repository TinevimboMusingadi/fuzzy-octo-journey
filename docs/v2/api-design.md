---
title: V2.0 Server-Side Form Selection API
overview: Design for selecting and running pre-built form schemas with the Dynamic Intake Form Agent.
---

## Goals

- Let a **server or CLI** choose *which* pre-built form (employment, housing, tax, healthcare) to run.
- Reuse the existing **LangGraph** (`create_intake_graph`) and **form schema** format.
- Keep the V1 behavior (sample schema in `main.py`) working while adding a clean path for V2.0.

---

## High-Level Flow

1. **Caller** (API route, CLI command, or script) chooses a `form_id`, e.g.:
   - `employment_onboarding`
   - `rental_application`
   - `tax_1040_mvp`
   - `healthcare_intake`
2. Server loads the corresponding **schema definition** (see `docs/v2/forms.md`), e.g. from:
   - Static JSON/YAML files in `forms/` or
   - A Python registry/dict in `src/config.py` or `src/forms.py`.
3. Server creates the **graph** via `create_intake_graph(...)`.
4. Server initializes **FormState** with:
   - `form_schema`: the loaded schema
   - `current_field_id`: first field’s `id`
   - `mode`: `"speed" | "quality" | "hybrid"`
5. Conversation loop:
   - Graph asks question(s) (`ask` node).
   - Client/user responds (web, CLI, or chat UI).
   - Server calls `graph.update_state(...)` with new user message and resumes execution.
6. When `is_complete` is true, read `collected_fields` and save via existing output handlers.

---

## Proposed API Shapes

### 1. Python Helper API

Add a small helper module (e.g., `src/forms_loader.py`) that centralizes form selection:

```python
from typing import Dict, Any

from src.forms_registry import get_form_schema  # new registry module
from src.graph import create_intake_graph
from src.config import AgentConfig
from src.nodes import set_config


def create_session(form_id: str, mode: str = "hybrid") -> Dict[str, Any]:
    """Create a new intake session for a specific pre-built form."""
    schema = get_form_schema(form_id)
    if not schema:
        raise ValueError(f"Unknown form_id: {form_id}")

    config = AgentConfig(default_mode=mode)
    set_config(config)

    graph = create_intake_graph(checkpointer=None)

    initial_state = {
        "messages": [],
        "form_schema": schema,
        "current_field_id": schema["fields"][0]["id"],
        "collected_fields": {},
        "validation_result": {},
        "clarification_count": 0,
        "is_complete": False,
        "notes": [],
        "mode": mode,
    }

    return {
        "graph": graph,
        "state": initial_state,
        "config": config,
    }
```

Notes:

- `get_form_schema(form_id)` would map IDs to the schemas defined in `docs/v2/forms.md` (implemented later as JSON files or Python dicts).
- The returned `graph` and `state` can be used by:
  - An HTTP handler
  - A CLI loop
  - A background worker.

### 2. HTTP API Sketch

Assuming a lightweight web framework (FastAPI/Flask/Django), the HTTP surface could look like:

- `POST /api/forms/start`
  - Body: `{ "form_id": "employment_onboarding", "mode": "hybrid" }`
  - Creates a session, returns:
    - `session_id`
    - First AI message (question)
- `POST /api/forms/answer`
  - Body: `{ "session_id": "...", "message": "user answer" }`
  - Feeds answer into the graph, advances, returns:
    - Next AI question (or final result when complete)
    - Flags like `is_complete`
- `GET /api/forms/result/{session_id}`
  - Returns:
    - Collected structured data
    - Notes, confidence scores, metadata (mode, form_id, timestamps)

This API only needs to **wrap the existing graph execution pattern** shown in `src/main.py`:

- Maintain a per-session state (using LangGraph checkpointing or another store).
- On each `/answer`, call `graph.update_state(...)` and then `graph.stream(...)` until the next `ask` or completion.

---

## CLI Flow Sketch (V2.0)

Extend or mirror `src/main.py` with a form‑selection CLI:

- Arguments:
  - `--form-id` (required in V2.0 path)
  - `--mode` (`speed | quality | hybrid`)
- Behavior:
  1. Load schema via `get_form_schema(form_id)`.
  2. Initialize graph and state (as in `create_session` above).
  3. Reuse the interactive loop pattern already in `run_interactive_demo`.

Example invocation:

```bash
python -m src.main_v2 --form-id employment_onboarding --mode hybrid
```

---

## How This Fits Existing Code

- `src/graph.py` and `src/nodes.py` **do not need structural changes** for V2.0:
  - They already operate on a generic `form_schema` and `current_field_id`.
- `src/modes.py` and `src/validation.py` already support:
  - The field types used in `docs/v2/forms.md`.
  - Rule-based validation and hybrid LLM vs. regex logic.
- V2.0 primarily adds:
  - A **catalog of schemas** (the pre-built forms).
  - A **loader/registry** that maps `form_id` → schema.
  - A **selection layer** (Python helper, HTTP API, or CLI entry point) that wires form choice into the existing graph.

---

## Future Extension Toward V2.1+

The same API shape can later support:

- A second “filling agent” that takes:
  - `form_id`
  - `user_profile` / context
  - raw document data
  - and outputs **pre-filled forms** for review.
- A `mode` or flag indicating:
  - `interactive_intake` (ask user questions)
  - `auto_fill` (agent fills on behalf of user, with occasional clarifications).

Those will layer on top of the same `form_id` + `form_schema` architecture established here.



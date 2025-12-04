---
title: V2.1 Dual-Agent Form Filling Design
overview: High-level design for a system where one agent converses with the user and another agent fills forms using user context and tools.
---

## 1. Goals

- Build on **V2.0** (pre-built forms + server-side selection) to support:
  - An agent that can **auto-fill** forms for the user using existing context and tools.
  - A conversational agent that can **ask clarifying questions** only when needed.
- Keep the **form schema** model from V2.0 (`form_id`, `form_schema`) so both agents share a single source of truth for what needs to be filled.
- Design first; implementation will come later, after V2.0 is wired into the codebase.

---

## 2. Core Concept: Two Roles

We introduce two logical roles (could be two LLM agents, or one model with two modes):

1. **Intake Agent (Question-Asker)**
   - Very close to the **current V1/V2.0 agent**.
   - Knows `form_schema` and current `FormState`.
   - Talks to the user:
     - Asks questions when a field is missing/uncertain.
     - Explains validation errors and requests clarification.

2. **Filler Agent (Form Filler)**
   - Given **user context** and the same `form_schema`, tries to:
     - Pre-fill as many fields as possible without asking the user.
     - Use tools to fetch additional data (if available).
     - Flag ambiguous or missing fields for the Intake Agent to ask about.

These roles **share the same form state**, but they are triggered at different times.

---

## 3. High-Level Flow (V2.1)

### 3.1 Inputs

- `form_id`: e.g., `employment_onboarding`, `rental_application`, etc.
- `form_schema`: loaded via V2.0 mechanisms.
- `user_context`:
  - Existing profile data (name, address, contact info).
  - Historical data (previous submissions, CRM, HRIS, EHR, etc.).
  - Optional external docs or APIs (e.g., uploaded paystubs, insurance cards).

### 3.2 Phases

1. **Auto-Fill Phase (Filler Agent)**
   - For each field in `form_schema`:
     - Filler Agent attempts to populate a value using `user_context` and tools.
     - Each field gets:
       - `value`
       - `raw` (source text or evidence)
       - `confidence` (0–1)
       - `notes` (e.g., “Guessed from profile address last updated 2 years ago”).
   - Output: a partially or fully filled `collected_fields` map.

2. **Gap & Ambiguity Detection**
   - Run **validation** (`validation.py`) on each auto-filled value.
   - Identify:
     - Fields still missing required values.
     - Values that fail validation.
     - Values with low confidence or ambiguous notes.
   - Mark these fields as needing **user interaction**.

3. **Interactive Phase (Intake Agent)**
   - Only for fields that:
     - Are required and missing.
     - Have `valid = False`.
     - Have `confidence < threshold` or flagged as ambiguous.
   - Use the existing conversational flow:
     - Ask question → process → validate → clarify/annotate → advance.
   - Filler Agent is not involved here; this is the **normal V2.0 behavior** but applied selectively.

4. **Review / Finalization**

   - Optionally show the user a **summary of auto-filled fields** plus fields they answered manually.
   - Allow a final confirmation or small edits before committing.

---

## 4. Architecture Sketch

### 4.1 State and Graphs

We keep existing concepts:

- `FormState` (see `src/types.py`):
  - `form_schema`
  - `current_field_id`
  - `collected_fields`
  - `validation_result`
  - `clarification_count`
  - `is_complete`
  - `mode` (`speed | quality | hybrid`)

For V2.1 we add **one new top-level phase state** concept:

- `fill_mode` (string or enum):
  - `"auto_fill"` – run Filler Agent.
  - `"interactive"` – hand off to Intake Agent.
  - `"review"` – final user review (optional).

Implementation options (to be decided during coding phase):

1. **Single graph with new nodes**
   - Add nodes like:
     - `auto_fill`
     - `detect_gaps`
   - Then transition into the existing nodes (`ask`, `process`, `validate`, etc.).

2. **Two graphs orchestrated by a controller**
   - A “meta-controller” runs:
     - Filler graph first (no user messages).
     - Then the existing intake graph.
   - Pros: keeps current graph mostly untouched.
   - Cons: more orchestration code.

The design assumes we **start with option 1** (extend the existing graph with new entry nodes) but will confirm this during implementation.

### 4.2 Filler Agent Interface

The Filler Agent will likely be implemented as:

- A helper function like:

```python
def auto_fill_form(
    form_schema: dict,
    user_context: dict,
    tools: "Toolbox",
) -> Dict[str, Any]:
    """Return a collected_fields-like mapping with value, confidence, raw, notes."""
```

Where `tools` could include:

- `get_profile_field(key)`
- `fetch_previous_submission(form_id)`
- `parse_document(image_or_pdf)`
- `call_external_api(name, params)`

The first version can be **simple**, using just `user_context` dict and no external tools.

---

## 5. Tooling & Data Sources (Conceptual)

For the first V2.1 design, we define conceptual tools (even if not implemented yet):

- **Profile Tool**
  - Input: field id or semantic description.
  - Output: candidate value from user profile + metadata (last updated, source).

- **History Tool**
  - Input: `form_id`, field id.
  - Output: last known value for this field from previous submissions.

- **Document Tool**
  - Input: reference to an uploaded document (image/PDF).
  - Output: structured fields parsed from the document.

The Filler Agent can call these tools (or stub functions) to build `collected_fields` before any conversation starts.

---

## 6. Confidence & Clarification Strategy

We introduce a **confidence-driven policy**:

- For each auto-filled field:
  - If `confidence >= 0.9` and validation passes:
    - Accept silently (no user question by default).
  - If `0.6 <= confidence < 0.9`:
    - Mark as “candidate”; may ask user for confirmation during review.
  - If `confidence < 0.6` or validation fails:
    - Add to **question queue** for the Intake Agent to ask about.

The threshold values (`0.9`, `0.6`) should be configurable (e.g., in `AgentConfig`).

---

## 7. User Experience Examples

### 7.1 Employment Onboarding Example

1. User logs in; system already knows:
   - Name, email, phone, current address.
2. User selects `employment_onboarding` form.
3. Filler Agent:
   - Auto-fills:
     - Name, email, phone from profile.
     - Possibly address from previous rental form.
     - Bank details from prior direct-deposit setup.
   - Flags:
     - I-9 document choice (unknown).
     - Document number and expiration (unknown).
4. Intake Agent only asks about:
   - I-9 document type.
   - Specific IDs and expiration.
   - Any missing or low-confidence fields (e.g., changed bank).

Result: fewer questions, faster completion.

### 7.2 Rental Application Example

1. `user_context` includes:
   - Previous rental application with landlord info.
   - Employment info used for I-9 or payroll.
2. Filler Agent:
   - Prefills current employer, job title, income, and possibly references.
3. Intake Agent:
   - Asks user only to confirm or update changed pieces (e.g., new landlord, new income).

---

## 8. Open Design Questions (for later)

These will be resolved when we move from design to implementation:

- Where to store and version **user_context**?
  - In-memory for demo vs. database for production.
- How to represent **provenance** (where each value came from) in `collected_fields`?
  - E.g., `source: "profile" | "history" | "document" | "user"`.
- How to let the user **override auto-filled values** during the review step?
- How aggressive the Filler Agent should be:
  - Only fill when 100% sure?
  - Or fill more and rely on the review step?

---

## 9. Implementation Phasing (after V2.0)

When we are ready to implement V2.1 in code, the steps will roughly be:

1. Add a simple `user_context` structure and pass it into the session creation path.
2. Implement a minimal `auto_fill_form` that:
   - Uses only `user_context` (no external tools yet).
   - Fills obvious fields (name, email, phone, address) for one form (e.g., employment).
3. Add graph entry nodes or a small controller to:
   - Run `auto_fill_form` once before the standard intake flow.
   - Mark which fields still need questions.
4. Add tests:
   - Auto-fill populates correct fields.
   - Intake Agent only asks about remaining ones.
5. Iterate toward more advanced tools (profile/history/documents) once the basic pattern works.



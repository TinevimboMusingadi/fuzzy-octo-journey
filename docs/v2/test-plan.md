---
title: V2.0 Test Plan
overview: Test strategy and concrete cases for pre-built forms and server-side form selection.
---

## 1. Scope

This test plan covers **V2.0**:

- Pre-built schemas defined in `docs/v2/forms.md`.
- Server-side form selection and session creation (as per `docs/v2/api-design.md`).
- End-to-end conversational runs of each form in **speed**, **quality** (where feasible), and **hybrid** modes.

V2.1+ (dual-agent auto-fill) will be covered in a separate test plan.

---

## 2. Test Types

### 2.1 Unit Tests

Focus on **pure-Python**, deterministic behavior:

- **Schema validity**
  - Each pre-built schema is a dict with:
    - Top-level `fields` list.
    - Each field has `id`, `field_type`, `label`, and `required`.
    - `field_type` is one of the supported types in `modes.py` / `validation.py`.
  - Validation of `validation` blocks:
    - Only known keys: `min`, `max`, `min_length`, `max_length`.
    - Types are numeric or integer where expected.

- **Loader/registry helpers** (when implemented):
  - `get_form_schema(form_id)` returns a dict for known IDs (`employment_onboarding`, `rental_application`, etc.).
  - Raises or returns `None` for unknown IDs.

- **Graph initialization with custom schemas**
  - Creating a `FormState` with a pre-built schema and passing it into `create_intake_graph` does not raise.
  - `advance_node` correctly walks through all fields in the schema.

Suggested locations:

- `tests/test_forms_schemas.py` – schema structure and compatibility checks.
- `tests/test_forms_loader.py` – loader/registry behavior.

### 2.2 Integration Tests (Graph-Level)

Run the actual LangGraph using **mock LLMs** or speed mode only:

- For each form `form_id`:
  - Build a **happy-path script** of user answers that should validate on first try.
  - Programmatically drive the graph:
    - Start at initial state with that form’s schema.
    - Feed answers one by one via `graph.update_state(...)`.
    - Let the graph stream until the next `ask` or completion.
  - Assert:
    - `is_complete` is `True` at the end.
    - `collected_fields` contains expected values and types.
    - No unexpected clarification loops.

Modes:

- Always run in **speed** mode for deterministic tests.
- Optionally add a smaller set of **quality/hybrid** tests using:
  - A fake/mocked LLM implementation that returns fixed JSON for prompts.

Suggested locations:

- `tests/test_forms_integration.py` – end-to-end flows per form.

### 2.3 API/CLI Contract Tests

Once an HTTP or CLI layer is added:

- **CLI tests**
  - Use `subprocess` or `pytest`’s CLI helpers to run:
    - `python -m src.main_v2 --form-id employment_onboarding --mode speed`
  - Feed scripted input and assert:
    - Expected questions appear in the transcript.
    - Process exits with code 0.

- **HTTP tests** (if applicable)
  - Use a framework’s test client (e.g., FastAPI `TestClient`) to:
    - `POST /api/forms/start` with a valid `form_id` and assert:
      - 200 OK.
      - JSON includes `session_id`, `form_id`, and initial question text.
    - `POST /api/forms/answer` repeatedly with scripted answers; assert:
      - Question/answer alternation works.
      - Final call returns `is_complete = true` and structured data.
    - Error cases:
      - Unknown `form_id` → 4xx with clear message.
      - Invalid `session_id` → 4xx.

---

## 3. Test Data and Cases

### 3.1 Employment / Onboarding

Happy path (speed mode):

- I-9:
  - Citizenship: `U.S. citizen`.
  - Document type: `U.S. passport`.
  - Passport number: `X12345678`.
  - Document expiration: valid ISO or natural-language date parsed to string.
- W-4:
  - Filing status: `Single or Married filing separately`.
  - Children under 17: `2`.
  - Other dependents: `1`.
  - Extra withholding: `50`.
- Direct deposit:
  - Bank name: `Chase`.
  - Account type: `Checking`.
  - Routing number: `021000021`.
  - Account number: `123456789`.

Key checks:

- All required fields present and `valid = True`.
- Numeric fields within configured `min`/`max` ranges.
- Routing number length exactly 9.

Edge/error cases:

- Missing required routing number → validation error and clarify loop.
- Invalid routing length (e.g., 8 digits) → clarify.
- Negative extra withholding → validation error.

### 3.2 Housing – Rental Application

Happy path:

- Provide full current and previous address text.
- Provide landlord names and phones.
- Provide employer, job title, HR phone, income.
- Provide at least one reference with phone/email.

Key checks:

- `address` fields are accepted with length ≥ 10.
- Phone and email fields pass format validators.
- Income is a positive number.

Edge cases:

- Missing current address (required) → clarify.
- Text too short for address (e.g., `NY`) → address min_length rule.

### 3.3 Government & Taxes – Form 1040 (MVP)

Happy path:

- Total wage income: `60000`.
- Other income: `500`.
- Deduction type: `Standard deduction`.
- Refund method: `Direct deposit`.
- Routing/account numbers populated.

Edge cases:

- Negative income → validation error.
- Refund method `Paper check` with routing/account filled – allowed but could generate annotations.

### 3.4 Healthcare – Patient Intake

Happy path:

- HIPAA consent: `Yes`.
- Authorized contacts: free-text list.
- Signature and date.
- Insurance member ID and optional group, provider phone, policy holder name.

Edge cases:

- HIPAA consent: ambiguous text (`maybe`) → boolean extraction should be `None` → clarify.
- Very long authorized contacts string → ensure `max_length` applied.

---

## 4. Non-Functional / Regression Checks

- **Performance**:
  - For each form in **speed mode**, end-to-end runs should complete within a reasonable response time (e.g., < 100ms per turn in local tests).
- **Stability**:
  - Running forms back-to-back with different `form_id` values should not leak state across sessions (especially if checkpointing is enabled).
- **Backward compatibility**:
  - Existing V1 tests (e.g., sample schema in `main.py`) must continue to pass.

---

## 5. Implementation Notes

- Prefer **pure speed-mode tests** for reliability.
- Where LLM behavior is needed:
  - Inject a **mock/fake LLM** (e.g., via dependency injection or monkeypatching `get_llm`) that returns deterministic JSON.
- Gradually add tests:
  1. Schema validity tests (quick feedback).
  2. Speed-mode happy-path integration for each form.
  3. Edge/clarification loops.
  4. API/CLI contracts once those surfaces exist.



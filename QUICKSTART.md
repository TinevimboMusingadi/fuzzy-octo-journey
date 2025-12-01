# Quick Start Guide

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (optional, for Quality mode):
Create a `.env` file:
```
OPENAI_API_KEY=your_api_key_here
DEFAULT_MODE=hybrid
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3
```

## Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Project Structure

```
.
├── src/
│   ├── types.py          # FormState type definition
│   ├── graph.py          # LangGraph definition
│   ├── nodes.py          # Node implementations
│   ├── modes.py          # Speed/Quality mode implementations
│   ├── validation.py     # Validation logic
│   ├── utils.py          # Helper functions
│   ├── config.py         # Configuration
│   └── main.py           # Entry point
├── tests/
│   ├── test_graph.py     # Graph tests
│   ├── test_nodes.py     # Node tests
│   ├── test_modes.py     # Mode tests
│   ├── test_validation.py # Validation tests
│   └── test_utils.py     # Utility tests
└── requirements.txt
```

## Usage

### Basic Usage

```python
from src.graph import create_intake_graph
from src.nodes import set_config
from src.config import AgentConfig

# Configure
config = AgentConfig(default_mode="speed")
set_config(config)

# Create graph
graph = create_intake_graph()

# Define form schema
schema = {
    "fields": [
        {"id": "name", "field_type": "text", "label": "Name", "required": True},
        {"id": "email", "field_type": "email", "label": "Email", "required": True}
    ]
}

# Initialize state
state = {
    "messages": [],
    "form_schema": schema,
    "current_field_id": "name",
    "collected_fields": {},
    "validation_result": {},
    "clarification_count": 0,
    "is_complete": False,
    "notes": [],
    "mode": "speed"
}

# Run graph
result = graph.invoke(state)
```

### Interactive Demo

Run the interactive demo:
```bash
python src/main.py
```

## Modes

### Speed Mode
- Template-based questions
- Regex extraction
- Rule-based validation
- Pattern-based annotation
- ~30-50ms per turn

### Quality Mode
- LLM-generated questions
- LLM extraction
- LLM verification
- LLM annotation
- ~700-800ms per turn

### Hybrid Mode (Recommended)
- Intelligently switches between Speed and Quality
- Uses LLM for complex fields and clarifications
- ~600-900ms per turn on average

## Testing Strategy

The project includes comprehensive unit tests:
- **71 tests** covering all components
- Tests for validation logic
- Tests for mode implementations
- Tests for node functions
- Tests for utility functions
- Tests for graph structure

Run tests after every change:
```bash
pytest tests/ -v
```

## Next Steps

1. Add your form schema
2. Configure the agent mode
3. Integrate with your application
4. Customize validation rules
5. Add custom field types


# Dynamic Intake Form Agent

A dual-mode LangGraph-based intake form agent supporting Speed Mode (~50ms/turn) and Quality Mode (~800ms/turn).

## Architecture

- **Speed Mode**: Template-driven, regex parsing, minimal LLM calls
- **Quality Mode**: LLM-powered generation and validation
- **Hybrid Mode**: Intelligent mode switching for optimal balance

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Add your OPENAI_API_KEY
```

3. Run tests:
```bash
pytest tests/ -v
```

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── graph.py              # LangGraph definition
│   ├── nodes.py              # Node implementations
│   ├── modes.py              # Speed/Quality mode implementations
│   ├── validation.py         # Validation logic
│   ├── config.py             # Configuration
│   └── utils.py              # Helper functions
├── tests/
│   ├── __init__.py
│   ├── test_graph.py
│   ├── test_nodes.py
│   ├── test_modes.py
│   └── test_validation.py
├── requirements.txt
└── README.md
```


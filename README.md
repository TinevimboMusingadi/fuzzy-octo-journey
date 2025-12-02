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
# Create .env file with your Google API key:
GOOGLE_API_KEY=your_api_key_here
DEFAULT_MODE=hybrid
LLM_MODEL=gemini-3-pro-preview
LLM_PROVIDER=google
LLM_TEMPERATURE=0.3

# Available Gemini models:
# - gemini-3-pro-preview (latest preview)
# - gemini-1.5-pro (stable)
# - gemini-1.5-flash (faster, lighter)
```

3. Run tests:
```bash
pytest tests/ -v
```

4. Run the interactive demo:
```bash
# From project root:
python src/main.py

# Or from src directory:
cd src
python main.py
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


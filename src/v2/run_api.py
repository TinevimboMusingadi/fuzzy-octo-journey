"""Simple script to run the V2.0 FastAPI server.

Usage:
    python -m src.v2.run_api
    # Or with uvicorn directly:
    uvicorn src.v2.api:app --reload --port 8000
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.v2.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


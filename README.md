# SuperTracer

A FastAPI middleware for tracing and logging HTTP requests to a SQLite database.

## Features

- Automatically logs all HTTP requests (method, URL, headers, timestamp)
- Provides a `/logs` endpoint to view request history in a web interface
- Easy integration with any FastAPI application

## Requirements

- Python 3.12 or higher (as specified in `pyproject.toml`)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

### Using uv (recommended)

```bash
# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package with dependencies
uv pip install -e . fastapi uvicorn
```

### Using pip

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package with dependencies
pip install -e . fastapi uvicorn
```

## Running the Example

After installation, run the example application:

```bash
python main.py
```

The server will start at `http://127.0.0.1:8000`. You can:

- Visit `http://127.0.0.1:8000/` - Returns a simple JSON response
- Visit `http://127.0.0.1:8000/items/42?q=test` - Example endpoint with parameters
- Visit `http://127.0.0.1:8000/logs` - View all logged requests

## Usage in Your Project

```python
from fastapi import FastAPI
from supertracer import SuperTracer

app = FastAPI()

# Initialize SuperTracer - this adds request logging middleware
# and creates a /logs endpoint
tracer = SuperTracer(app, db_path="requests.db")

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

## License

MIT

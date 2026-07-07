# Restaurant Local Hardware Node

FastAPI-based local bridge for Iranian POS hardware integrations.

## Features
- Localhost-only API with API key auth
- Pluggable payment drivers
- Health endpoint for dashboard
- Mock driver for development

## Run

```bash
cd apps/restaurant/local_hardware_node
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LOCAL_NODE_API_KEY=change-me
uvicorn app.main:app --host 127.0.0.1 --port 27100
```

## Environment Variables
- `LOCAL_NODE_API_KEY` (required)
- `LOCAL_NODE_PAYMENT_DRIVER` (default: `mock`)
- `LOCAL_NODE_ALLOWED_HOSTS` (default: `127.0.0.1,localhost`)
- `LOCAL_NODE_VERSION` (optional)

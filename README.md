# FastAPI + JWT + MCP Example

## Install
\\\
pip install -r requirements.txt
\\\

## Run
\\\
uvicorn app.main:app --reload
\\\

## Endpoints
- POST /register – JSON {username, password}
- POST /login – form-data credentials → returns JWT
- GET /protected – requires Authorization: Bearer <token>
- MCP tools at /mcp – protected via the same JWT

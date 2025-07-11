import uvicorn
from fastapi import FastAPI
from .routers.auth_router import router as auth_router
from .routers.protected_router import router as protected_router
from .routers.llm_router import router as llm_router
from .mcp_server import app, mcp # same app instance

# app = mcp_app
app.include_router(auth_router)
app.include_router(protected_router)
app.include_router(llm_router)
mcp.setup_server()

if __name__ == '__main__':
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True)

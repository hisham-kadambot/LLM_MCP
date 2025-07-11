
from fastapi import FastAPI, Depends
from fastapi_mcp import FastApiMCP, AuthConfig
from .auth import verify_jwt_token
from .llm_interface import get_llm_interface
from .routers.google_drive_router import router as google_drive_router
from typing import Optional

app = FastAPI()

mcp = FastApiMCP(
    app,
    name="Protected MCP",
    auth_config=AuthConfig(dependencies=[Depends(verify_jwt_token)]),
    # mcp_dependencies=[Depends(verify_jwt_token)],  # enforce auth on all MCP calls
    include_operations=["dummy_tool", "llm_chat_tool", "google_drive_authenticate", "google_drive_create_folder", "google_drive_upload_file", "google_drive_upload_content", "google_drive_download_file", "google_drive_list_files", "google_drive_search_files", "google_drive_delete_file", "google_drive_share_file", "google_drive_create_shared_link", "google_drive_create_customer_folder", "google_drive_upload_customer_document", "google_drive_get_customer_documents", "google_drive_status"],
    describe_all_responses=True,     # Include all possible response schemas in tool descriptions
    describe_full_response_schema=True  # Include full JSON schema in tool descriptions
)

@app.get("/hello", operation_id="dummy_tool")
def dummy_tool(username: str = Depends(verify_jwt_token)) -> str:
    return f"MCP says hi to {username}"

# Auto-generated operation_id (something like "read_user_users__user_id__get")
@app.get("/users/{user_id}")
async def read_user(user_id: int):
    return {"user_id": user_id}

# Explicit operation_id (tool will be named "get_user_info")
@app.get("/users/{user_id}", operation_id="get_user_info")
async def read_user(user_id: int):
    return {"user_id": user_id}
    
@app.post("/chat", operation_id="llm_chat_tool")
def llm_chat_tool(
    message: str,
    model_name: str = "openai",
    username: str = Depends(verify_jwt_token),
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> str:
    """
    Send a message to an LLM (OpenAI or Anthropic) and get a response.
    
    Args:
        message: The message to send to the LLM
        model_name: The model to use ('openai', 'anthropic', 'gpt', 'claude', etc.)
        username: The authenticated username (from JWT token)
        max_tokens: Maximum tokens for the response (optional)
        temperature: Temperature for response generation (optional)
        
    Returns:
        The response from the LLM
    """
    try:
        # Get the LLM interface using the factory function
        llm_interface = get_llm_interface(username, model_name)
        
        # Prepare kwargs for the chat method
        kwargs = {}
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        if temperature is not None:
            kwargs['temperature'] = temperature
            
        # Send the message and get response
        response = llm_interface.chat(message, **kwargs)
        return response
        
    except Exception as e:
        return f"Error: {str(e)}"

# mcp.auth_config.dependencies.append(
#     DependsSkipList(["list_tools", "call_tool"])
# )

# Add tools to the MCP server
mcp.tools.append(dummy_tool)
mcp.tools.append(llm_chat_tool)

# Include Google Drive router
app.include_router(google_drive_router)

mcp.mount()

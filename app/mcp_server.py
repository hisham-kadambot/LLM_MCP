
from fastapi import FastAPI, Depends
from fastapi_mcp import FastApiMCP, AuthConfig
from .auth import verify_jwt_token
from .llm_interface import get_llm_interface
from .routers.google_drive_router import router as google_drive_router
from typing import Optional
import os
from app.services.google_drive_service import google_drive_service
import logging
logging.basicConfig(level=logging.WARNING)

app = FastAPI()

mcp = FastApiMCP(
    app,
    name="Protected MCP",
    auth_config=AuthConfig(dependencies=[Depends(verify_jwt_token)]),
    # mcp_dependencies=[Depends(verify_jwt_token)],  # enforce auth on all MCP calls
    include_operations=["dummy_tool", "llm_chat_tool", "llm_paraphrase_tool", "google_drive_authenticate", "google_drive_create_folder", "google_drive_upload_file", "google_drive_upload_content", "google_drive_download_file", "google_drive_list_files", "google_drive_search_files", "google_drive_delete_file", "google_drive_share_file", "google_drive_create_shared_link", "google_drive_create_customer_folder", "google_drive_upload_customer_document", "google_drive_get_customer_documents", "google_drive_status"],
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
    model_name: str = "llama2",
    username: str = Depends(verify_jwt_token),
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> str:
    """
    Send a message to an LLM (OpenAI or Anthropic) and get a response.
    Supports simple chat commands for Google Drive operations.
    Type 'help' for a list of supported commands.
    """
    import base64
    import tempfile
    import os
    try:
        msg = message.strip()
        lower_msg = msg.lower()
        # Help command
        if lower_msg in ["help", "google drive help", "drive help"]:
            return (
                "Google Drive commands:\n"
                "- authenticate google drive\n"
                "- create folder <folder_name> [parent_folder_id]\n"
                "- upload file <file_path> [folder_id]\n"
                "- upload content <file_name> <content> [folder_id]\n"
                "- list files [folder_id]\n"
                "- search files <query>\n"
                "- delete file <file_id>\n"
                "- delete file by name <file_name>\n"
                "- delete folder by name <folder_name>\n"
                "- share file <file_id> <email> [role] [notify]\n"
                "- create shared link <file_id> [permission]\n"
                "- create customer folder <customer_name> <customer_email>\n"
                "- upload customer document <customer_folder_id> <document_name> <document_content> [document_type]\n"
                "- get customer documents <customer_folder_id>\n"
                "- google drive status\n"
                "- download file <file_id>\n"
                "- download file by name <file_name>\n"
                "- help\n"
            )
        # Authenticate
        if lower_msg.startswith("authenticate google drive"):
            success = google_drive_service.authenticate()
            return "Authentication successful" if success else "Authentication failed"
        # Create folder
        if lower_msg.startswith("create folder"):
            parts = msg.split()
            if len(parts) < 3:
                return "Usage: create folder <folder_name> [parent_folder_id]"
            folder_name = parts[2]
            parent_folder_id = parts[3] if len(parts) > 3 else None
            folder = google_drive_service.create_folder(folder_name, parent_folder_id)
            return f"Folder created: {folder}"
        # Upload file (by path)
        if lower_msg.startswith("upload file"):
            parts = msg.split()
            if len(parts) < 3:
                return "Usage: upload file <file_path> [folder_id]"
            file_path = parts[2]
            folder_id = parts[3] if len(parts) > 3 else None
            if not os.path.exists(file_path):
                return f"File not found: {file_path}"
            result = google_drive_service.upload_file(file_path, folder_id)
            return f"File uploaded: {result}"
        # Upload content (base64 or plain text)
        if lower_msg.startswith("upload content"):
            parts = msg.split(maxsplit=4)
            if len(parts) < 4:
                return "Usage: upload content <file_name> <content> [folder_id]"
            file_name = parts[2]
            content = parts[3]
            folder_id = parts[4] if len(parts) > 4 else None
            # Try to decode as base64, fallback to utf-8
            try:
                file_content = base64.b64decode(content)
            except Exception:
                file_content = content.encode("utf-8")
            result = google_drive_service.upload_file_content(file_content, file_name, folder_id)
            return f"Content uploaded: {result}"
        # List files
        if lower_msg.startswith("list files"):
            parts = msg.split()
            folder_id = parts[2] if len(parts) > 2 else None
            files = google_drive_service.list_files(folder_id)
            return f"Files: {files}"
        # Search files
        if lower_msg.startswith("search files"):
            parts = msg.split(maxsplit=2)
            if len(parts) < 3:
                return "Usage: search files <query>"
            query = parts[2]
            files = google_drive_service.search_files(query)
            return f"Search results: {files}"
        # Delete file by name (must come before generic delete file)
        if lower_msg.startswith("delete file by name"):
            prefix = "delete file by name"
            name = msg[len(prefix):].strip()
            print(f"[DEBUG] delete file by name: '{name}'")
            if not name:
                return "Usage: delete file by name <file_name>"
            matches = google_drive_service.search_files(name)
            files = [f for f in matches if f.get('mimeType') != 'application/vnd.google-apps.folder']
            if not files:
                return f"No file found with the name: {name}"
            if len(files) == 1:
                file_id = files[0]['id']
                success = google_drive_service.delete_file(file_id)
                return "File deleted" if success else "Failed to delete file"
            options = [f"Name: {f['name']}, ID: {f['id']}, Created: {f.get('createdTime', 'N/A')}" for f in files]
            return f"Multiple files found for '{name}':\n" + "\n".join(options)
        # Delete folder by name (must come before generic delete file)
        if lower_msg.startswith("delete folder by name"):
            prefix = "delete folder by name"
            name = msg[len(prefix):].strip()
            print(f"[DEBUG] delete folder by name: '{name}'")
            if not name:
                return "Usage: delete folder by name <folder_name>"
            matches = google_drive_service.search_files(name)
            folders = [f for f in matches if f.get('mimeType') == 'application/vnd.google-apps.folder']
            if not folders:
                return f"No folder found with the name: {name}"
            if len(folders) == 1:
                folder_id = folders[0]['id']
                success = google_drive_service.delete_file(folder_id)
                return "Folder deleted" if success else "Failed to delete folder"
            options = [f"Name: {f['name']}, ID: {f['id']}, Created: {f.get('createdTime', 'N/A')}" for f in folders]
            return f"Multiple folders found for '{name}':\n" + "\n".join(options)
        # Delete file by ID (generic, must come after the above)
        if lower_msg.startswith("delete file"):
            parts = msg.split()
            print(f"[DEBUG] delete file parts: {parts}")
            if len(parts) < 3:
                return "Usage: delete file <file_id>"
            file_id = parts[2]
            success = google_drive_service.delete_file(file_id)
            return "File deleted" if success else "Failed to delete file"
        # Share file
        if lower_msg.startswith("share file"):
            parts = msg.split()
            if len(parts) < 4:
                return "Usage: share file <file_id> <email> [role] [notify]"
            file_id = parts[2]
            email = parts[3]
            role = parts[4] if len(parts) > 4 else "reader"
            notify = parts[5].lower() == "true" if len(parts) > 5 else True
            permission = google_drive_service.share_file(file_id, email, role, notify)
            return f"File shared: {permission}"
        # Create shared link
        if lower_msg.startswith("create shared link"):
            parts = msg.split()
            if len(parts) < 4:
                return "Usage: create shared link <file_id> [permission]"
            file_id = parts[3]
            permission = parts[4] if len(parts) > 4 else "reader"
            link = google_drive_service.create_shared_link(file_id, permission)
            return f"Shared link: {link}"
        # Create customer folder
        if lower_msg.startswith("create customer folder"):
            parts = msg.split()
            if len(parts) < 5:
                return "Usage: create customer folder <customer_name> <customer_email>"
            customer_name = parts[3]
            customer_email = parts[4]
            folder_structure = google_drive_service.create_customer_support_folder(customer_name, customer_email)
            return f"Customer folder created: {folder_structure}"
        # Upload customer document
        if lower_msg.startswith("upload customer document"):
            parts = msg.split(maxsplit=5)
            if len(parts) < 5:
                return "Usage: upload customer document <customer_folder_id> <document_name> <document_content> [document_type]"
            customer_folder_id = parts[3]
            document_name = parts[4]
            document_content = parts[5] if len(parts) > 5 else ""
            document_type = parts[6] if len(parts) > 6 else "documents"
            # Try to decode as base64, fallback to utf-8
            try:
                doc_content_bytes = base64.b64decode(document_content)
            except Exception:
                doc_content_bytes = document_content.encode("utf-8")
            result = google_drive_service.upload_customer_document(customer_folder_id, doc_content_bytes, document_name, document_type)
            return f"Customer document uploaded: {result}"
        # Get customer documents
        if lower_msg.startswith("get customer documents"):
            parts = msg.split()
            if len(parts) < 4:
                return "Usage: get customer documents <customer_folder_id>"
            customer_folder_id = parts[3]
            documents = google_drive_service.get_customer_documents(customer_folder_id)
            return f"Customer documents: {documents}"
        # Google Drive status
        if lower_msg.startswith("google drive status"):
            status = {
                "authenticated": google_drive_service.authenticated,
                "service_available": google_drive_service.service is not None
            }
            return f"Google Drive status: {status}"
        # Download file by name (existing logic)
        if lower_msg.startswith("download file by name "):
            file_name = msg[len("download file by name "):].strip()
            if not file_name:
                return "Error: No file name provided. Usage: download file by name <file_name>"
            matches = google_drive_service.search_files(file_name)
            if not matches:
                return "no file found"
            if len(matches) == 1:
                file_id = matches[0]['id']
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, f"downloaded_{file_id}")
                try:
                    google_drive_service.download_file(file_id, output_path=output_path)
                    return f"File downloaded successfully to: {output_path}"
                except Exception as e:
                    return f"Error downloading file: {e}"
            else:
                options = [f"Name: {f['name']}, ID: {f['id']}, Created: {f.get('createdTime', 'N/A')}" for f in matches]
                return "Multiple files found:\n" + "\n".join(options)
        # Download file by id (existing logic)
        if lower_msg.startswith("download file "):
            file_id = msg[len("download file "):].strip()
            if not file_id:
                return "Error: No file_id provided. Usage: download file <file_id>"
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"downloaded_{file_id}")
            try:
                google_drive_service.download_file(file_id, output_path=output_path)
                return f"File downloaded successfully to: {output_path}"
            except Exception as e:
                return f"Error downloading file: {e}"
        # Normal LLM chat fallback
        llm_interface = get_llm_interface(username, model_name)
        kwargs = {}
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        if temperature is not None:
            kwargs['temperature'] = temperature
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

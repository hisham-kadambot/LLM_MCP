"""
Google Drive Router for MCP Server
Provides endpoints for Google Drive operations
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, List, Dict, Any
import base64
import json

from ..auth import verify_jwt_token
from ..services.google_drive_service import google_drive_service

router = APIRouter(prefix="/google-drive", tags=["Google Drive"])

@router.post("/authenticate", operation_id="google_drive_authenticate")
async def authenticate_google_drive(username: str = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """
    Authenticate with Google Drive API
    
    Args:
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing authentication status
    """
    try:
        success = google_drive_service.authenticate()
        return {
            "authenticated": success,
            "message": "Authentication successful" if success else "Authentication failed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

@router.post("/create-folder", operation_id="google_drive_create_folder")
async def create_folder(
    folder_name: str,
    parent_folder_id: Optional[str] = None,
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Create a new folder in Google Drive
    
    Args:
        folder_name: Name of the folder to create
        parent_folder_id: ID of parent folder (optional)
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing folder information
    """
    try:
        folder = google_drive_service.create_folder(folder_name, parent_folder_id)
        return folder
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")

@router.post("/upload-file", operation_id="google_drive_upload_file")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Upload a file to Google Drive
    
    Args:
        file: File to upload
        folder_id: ID of folder to upload to (optional)
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing uploaded file information
    """
    try:
        content = await file.read()
        result = google_drive_service.upload_file_content(
            content, 
            file.filename, 
            folder_id,
            file.content_type or 'application/octet-stream'
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.post("/upload-content", operation_id="google_drive_upload_content")
async def upload_content(
    content: str = Form(...),
    file_name: str = Form(...),
    folder_id: Optional[str] = Form(None),
    mime_type: str = Form("text/plain"),
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Upload content directly to Google Drive
    
    Args:
        content: File content (base64 encoded)
        file_name: Name of the file
        folder_id: ID of folder to upload to (optional)
        mime_type: MIME type of the file
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing uploaded file information
    """
    try:
        # Decode base64 content
        file_content = base64.b64decode(content)
        result = google_drive_service.upload_file_content(
            file_content, 
            file_name, 
            folder_id,
            mime_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading content: {str(e)}")

@router.get("/download-file/{file_id}", operation_id="google_drive_download_file")
async def download_file(
    file_id: str,
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Download a file from Google Drive
    
    Args:
        file_id: ID of the file to download
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing file content and metadata
    """
    try:
        content = google_drive_service.download_file(file_id)
        return {
            "file_id": file_id,
            "content": base64.b64encode(content).decode('utf-8'),
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@router.get("/list-files", operation_id="google_drive_list_files")
async def list_files(
    folder_id: Optional[str] = None,
    query: Optional[str] = None,
    page_size: int = 100,
    username: str = Depends(verify_jwt_token)
) -> List[Dict[str, Any]]:
    """
    List files and folders in Google Drive
    
    Args:
        folder_id: ID of folder to list (optional)
        query: Custom query string (optional)
        page_size: Number of items per page
        username: Authenticated username (from JWT token)
        
    Returns:
        List of file/folder information
    """
    try:
        files = google_drive_service.list_files(folder_id, query, page_size)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@router.get("/search-files", operation_id="google_drive_search_files")
async def search_files(
    query: str,
    page_size: int = 100,
    username: str = Depends(verify_jwt_token)
) -> List[Dict[str, Any]]:
    """
    Search for files in Google Drive
    
    Args:
        query: Search query
        page_size: Number of items per page
        username: Authenticated username (from JWT token)
        
    Returns:
        List of matching files
    """
    try:
        files = google_drive_service.search_files(query, page_size)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")

@router.delete("/delete-file/{file_id}", operation_id="google_drive_delete_file")
async def delete_file(
    file_id: str,
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Delete a file from Google Drive
    
    Args:
        file_id: ID of the file to delete
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing deletion status
    """
    try:
        success = google_drive_service.delete_file(file_id)
        return {"success": success, "message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@router.post("/share-file", operation_id="google_drive_share_file")
async def share_file(
    file_id: str,
    email: str,
    role: str = "reader",
    notify: bool = True,
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Share a file with another user
    
    Args:
        file_id: ID of the file to share
        email: Email address of the user to share with
        role: Role to grant ('reader', 'writer', 'commenter', 'owner')
        notify: Whether to send notification email
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing permission information
    """
    try:
        permission = google_drive_service.share_file(file_id, email, role, notify)
        return permission
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sharing file: {str(e)}")

@router.post("/create-shared-link", operation_id="google_drive_create_shared_link")
async def create_shared_link(
    file_id: str,
    permission: str = "reader",
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Create a shared link for a file
    
    Args:
        file_id: ID of the file
        permission: Permission level ('reader', 'writer', 'commenter')
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing shared link
    """
    try:
        link = google_drive_service.create_shared_link(file_id, permission)
        return {"file_id": file_id, "shared_link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating shared link: {str(e)}")

# Customer Support Specific Endpoints

@router.post("/create-customer-folder", operation_id="google_drive_create_customer_folder")
async def create_customer_folder(
    customer_name: str,
    customer_email: str,
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Create a customer support folder structure
    
    Args:
        customer_name: Name of the customer
        customer_email: Email of the customer
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing folder structure information
    """
    try:
        folder_structure = google_drive_service.create_customer_support_folder(
            customer_name, customer_email
        )
        return folder_structure
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating customer folder: {str(e)}")

@router.post("/upload-customer-document", operation_id="google_drive_upload_customer_document")
async def upload_customer_document(
    customer_folder_id: str,
    document_content: str = Form(...),
    document_name: str = Form(...),
    document_type: str = Form("documents"),
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Upload a customer document to the appropriate folder
    
    Args:
        customer_folder_id: ID of the customer's main folder
        document_content: Document content (base64 encoded)
        document_name: Name of the document
        document_type: Type of document ('documents', 'contracts', 'tickets', 'communications')
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing uploaded file information
    """
    try:
        # Decode base64 content
        content = base64.b64decode(document_content)
        result = google_drive_service.upload_customer_document(
            customer_folder_id, content, document_name, document_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading customer document: {str(e)}")

@router.get("/get-customer-documents/{customer_folder_id}", operation_id="google_drive_get_customer_documents")
async def get_customer_documents(
    customer_folder_id: str,
    username: str = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Get all documents for a customer organized by type
    
    Args:
        customer_folder_id: ID of the customer's main folder
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing documents organized by type
    """
    try:
        documents = google_drive_service.get_customer_documents(customer_folder_id)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting customer documents: {str(e)}")

@router.get("/status", operation_id="google_drive_status")
async def get_google_drive_status(username: str = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """
    Get Google Drive service status
    
    Args:
        username: Authenticated username (from JWT token)
        
    Returns:
        Dict containing service status
    """
    return {
        "authenticated": google_drive_service.authenticated,
        "service_available": google_drive_service.service is not None
    } 
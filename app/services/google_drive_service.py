"""
Google Drive Service for MCP Server
Handles authentication, file operations, and customer support features
"""

import os
import json
import base64
from typing import List, Dict, Optional, Any, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io

# Google Drive API scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',  # Access to files created by the app
    'https://www.googleapis.com/auth/drive.readonly',  # Read-only access to files
    'https://www.googleapis.com/auth/drive.metadata.readonly'  # Read metadata only
]

class GoogleDriveService:
    """
    Google Drive service for handling file operations and customer support features
    """
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        """
        Initialize Google Drive service
        
        Args:
            credentials_path: Path to Google OAuth credentials file
            token_path: Path to store/retrieve OAuth token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.authenticated = False
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API using OAuth2
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                print(f"Error loading existing token: {e}")
                creds = None
        
        # If no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}. "
                        "Please download credentials.json from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            # Save the credentials for the next run
            try:
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Error saving token: {e}")
        
        try:
            self.service = build('drive', 'v3', credentials=creds)
            self.authenticated = True
            return True
        except Exception as e:
            print(f"Error building Drive service: {e}")
            self.authenticated = False
            return False
    
    def ensure_authenticated(self):
        """Ensure service is authenticated before making API calls"""
        if not self.authenticated or not self.service:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Google Drive")
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new folder in Google Drive
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: ID of parent folder (optional)
            
        Returns:
            Dict containing folder information
        """
        self.ensure_authenticated()
        
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]
        
        try:
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            return {
                'id': folder.get('id'),
                'name': folder.get('name'),
                'webViewLink': folder.get('webViewLink'),
                'type': 'folder'
            }
        except HttpError as error:
            raise Exception(f"Error creating folder: {error}")
    
    def upload_file(self, file_path: str, folder_id: Optional[str] = None, 
                   file_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to Google Drive
        
        Args:
            file_path: Path to the file to upload
            folder_id: ID of folder to upload to (optional)
            file_name: Custom name for the file (optional)
            
        Returns:
            Dict containing file information
        """
        self.ensure_authenticated()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_name = file_name or os.path.basename(file_path)
        
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        try:
            with open(file_path, 'rb') as file:
                media = MediaIoBaseUpload(
                    file, 
                    mimetype='application/octet-stream',
                    resumable=True
                )
                
                file_obj = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,size,webViewLink,createdTime,modifiedTime'
                ).execute()
                
                return {
                    'id': file_obj.get('id'),
                    'name': file_obj.get('name'),
                    'size': file_obj.get('size'),
                    'webViewLink': file_obj.get('webViewLink'),
                    'createdTime': file_obj.get('createdTime'),
                    'modifiedTime': file_obj.get('modifiedTime'),
                    'type': 'file'
                }
        except HttpError as error:
            raise Exception(f"Error uploading file: {error}")
    
    def upload_file_content(self, content: bytes, file_name: str, 
                           folder_id: Optional[str] = None, 
                           mime_type: str = 'application/octet-stream') -> Dict[str, Any]:
        """
        Upload file content directly to Google Drive
        
        Args:
            content: File content as bytes
            file_name: Name of the file
            folder_id: ID of folder to upload to (optional)
            mime_type: MIME type of the file
            
        Returns:
            Dict containing file information
        """
        self.ensure_authenticated()
        
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        try:
            media = MediaIoBaseUpload(
                io.BytesIO(content),
                mimetype=mime_type,
                resumable=True
            )
            
            file_obj = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,webViewLink,createdTime,modifiedTime'
            ).execute()
            
            return {
                'id': file_obj.get('id'),
                'name': file_obj.get('name'),
                'size': file_obj.get('size'),
                'webViewLink': file_obj.get('webViewLink'),
                'createdTime': file_obj.get('createdTime'),
                'modifiedTime': file_obj.get('modifiedTime'),
                'type': 'file'
            }
        except HttpError as error:
            raise Exception(f"Error uploading file content: {error}")
    
    def download_file(self, file_id: str, output_path: Optional[str] = None, export_mime_type: Optional[str] = None) -> bytes:
        """
        Download a file from Google Drive
        
        Args:
            file_id: ID of the file to download
            output_path: Path to save the file (optional)
            export_mime_type: MIME type to export Google Docs/Sheets/Slides files (optional)
            
        Returns:
            File content as bytes
        """
        self.ensure_authenticated()
        try:
            # Get file metadata to check MIME type
            file_metadata = self.service.files().get(fileId=file_id, fields='mimeType').execute()
            mime_type = file_metadata.get('mimeType')
            # If it's a Google Docs/Sheets/Slides file, use export
            if mime_type == 'application/vnd.google-apps.document':
                export_mime_type = export_mime_type or 'application/pdf'
                request = self.service.files().export_media(fileId=file_id, mimeType=export_mime_type)
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                export_mime_type = export_mime_type or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                request = self.service.files().export_media(fileId=file_id, mimeType=export_mime_type)
            elif mime_type == 'application/vnd.google-apps.presentation':
                export_mime_type = export_mime_type or 'application/pdf'
                request = self.service.files().export_media(fileId=file_id, mimeType=export_mime_type)
            else:
                # For binary files, use the normal download
                request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            content = file_content.getvalue()
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(content)
            return content
        except HttpError as error:
            raise Exception(f"Error downloading file: {error}")
    
    def list_files(self, folder_id: Optional[str] = None, 
                   query: Optional[str] = None, 
                   page_size: int = 100) -> List[Dict[str, Any]]:
        """
        List files and folders in Google Drive
        
        Args:
            folder_id: ID of folder to list (optional)
            query: Custom query string (optional)
            page_size: Number of items per page
            
        Returns:
            List of file/folder information
        """
        self.ensure_authenticated()
        
        # Build query
        if folder_id:
            base_query = f"'{folder_id}' in parents"
        else:
            base_query = "trashed=false"
        
        if query:
            final_query = f"{base_query} and {query}"
        else:
            final_query = base_query
        
        try:
            results = self.service.files().list(
                q=final_query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents)"
            ).execute()
            
            items = results.get('files', [])
            
            return [{
                'id': item.get('id'),
                'name': item.get('name'),
                'mimeType': item.get('mimeType'),
                'size': item.get('size'),
                'createdTime': item.get('createdTime'),
                'modifiedTime': item.get('modifiedTime'),
                'webViewLink': item.get('webViewLink'),
                'parents': item.get('parents', []),
                'type': 'folder' if item.get('mimeType') == 'application/vnd.google-apps.folder' else 'file'
            } for item in items]
        except HttpError as error:
            raise Exception(f"Error listing files: {error}")
    
    def search_files(self, query: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Search for files in Google Drive
        
        Args:
            query: Search query
            page_size: Number of items per page
            
        Returns:
            List of matching files
        """
        self.ensure_authenticated()
        
        try:
            results = self.service.files().list(
                q=f"name contains '{query}' and trashed=false",
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents)"
            ).execute()
            
            items = results.get('files', [])
            
            return [{
                'id': item.get('id'),
                'name': item.get('name'),
                'mimeType': item.get('mimeType'),
                'size': item.get('size'),
                'createdTime': item.get('createdTime'),
                'modifiedTime': item.get('modifiedTime'),
                'webViewLink': item.get('webViewLink'),
                'parents': item.get('parents', []),
                'type': 'folder' if item.get('mimeType') == 'application/vnd.google-apps.folder' else 'file'
            } for item in items]
        except HttpError as error:
            raise Exception(f"Error searching files: {error}")
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            True if successful
        """
        self.ensure_authenticated()
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as error:
            raise Exception(f"Error deleting file: {error}")
    
    def share_file(self, file_id: str, email: str, role: str = 'reader', 
                   notify: bool = True) -> Dict[str, Any]:
        """
        Share a file with another user
        
        Args:
            file_id: ID of the file to share
            email: Email address of the user to share with
            role: Role to grant ('reader', 'writer', 'commenter', 'owner')
            notify: Whether to send notification email
            
        Returns:
            Dict containing permission information
        """
        self.ensure_authenticated()
        
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }
        
        try:
            permission_obj = self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=notify,
                fields='id,emailAddress,role'
            ).execute()
            
            return {
                'id': permission_obj.get('id'),
                'emailAddress': permission_obj.get('emailAddress'),
                'role': permission_obj.get('role')
            }
        except HttpError as error:
            raise Exception(f"Error sharing file: {error}")
    
    def create_customer_support_folder(self, customer_name: str, 
                                     customer_email: str) -> Dict[str, Any]:
        """
        Create a customer support folder structure
        
        Args:
            customer_name: Name of the customer
            customer_email: Email of the customer
            
        Returns:
            Dict containing folder structure information
        """
        self.ensure_authenticated()
        
        # Create main customer folder
        customer_folder = self.create_folder(f"Customer Support - {customer_name}")
        
        # Create subfolders for different types of documents
        subfolders = {
            'documents': self.create_folder('Documents', customer_folder['id']),
            'contracts': self.create_folder('Contracts', customer_folder['id']),
            'tickets': self.create_folder('Support Tickets', customer_folder['id']),
            'communications': self.create_folder('Communications', customer_folder['id'])
        }
        
        return {
            'customer_folder': customer_folder,
            'subfolders': subfolders,
            'customer_name': customer_name,
            'customer_email': customer_email
        }
    
    def upload_customer_document(self, customer_folder_id: str, 
                               document_content: bytes, 
                               document_name: str,
                               document_type: str = 'documents') -> Dict[str, Any]:
        """
        Upload a customer document to the appropriate folder
        
        Args:
            customer_folder_id: ID of the customer's main folder
            document_content: Document content as bytes
            document_name: Name of the document
            document_type: Type of document ('documents', 'contracts', 'tickets', 'communications')
            
        Returns:
            Dict containing uploaded file information
        """
        self.ensure_authenticated()
        
        # Find the appropriate subfolder
        subfolders = self.list_files(customer_folder_id)
        target_folder_id = None
        
        for folder in subfolders:
            if folder['type'] == 'folder' and folder['name'].lower() == document_type.lower():
                target_folder_id = folder['id']
                break
        
        if not target_folder_id:
            # Create the subfolder if it doesn't exist
            new_folder = self.create_folder(document_type.title(), customer_folder_id)
            target_folder_id = new_folder['id']
        
        # Upload the document
        return self.upload_file_content(document_content, document_name, target_folder_id)
    
    def get_customer_documents(self, customer_folder_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all documents for a customer organized by type
        
        Args:
            customer_folder_id: ID of the customer's main folder
            
        Returns:
            Dict containing documents organized by type
        """
        self.ensure_authenticated()
        
        # Get all subfolders
        subfolders = self.list_files(customer_folder_id)
        documents = {}
        
        for folder in subfolders:
            if folder['type'] == 'folder':
                folder_name = folder['name'].lower()
                folder_files = self.list_files(folder['id'])
                documents[folder_name] = folder_files
        
        return documents
    
    def create_shared_link(self, file_id: str, 
                          permission: str = 'reader') -> str:
        """
        Create a shared link for a file
        
        Args:
            file_id: ID of the file
            permission: Permission level ('reader', 'writer', 'commenter')
            
        Returns:
            Shared link URL
        """
        self.ensure_authenticated()
        
        try:
            # Create permission for anyone with the link
            permission_obj = {
                'type': 'anyone',
                'role': permission
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission_obj
            ).execute()
            
            # Get the file to return the webViewLink
            file_obj = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            
            return file_obj.get('webViewLink', '')
        except HttpError as error:
            raise Exception(f"Error creating shared link: {error}")

# Global instance for the MCP server
google_drive_service = GoogleDriveService() 
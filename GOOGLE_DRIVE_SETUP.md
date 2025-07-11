# Google Drive Integration Setup Guide

This guide explains how to set up and use Google Drive integration with your MCP server for customer support operations.

## Overview

The Google Drive integration provides the following capabilities:

- **File Storage & Retrieval**: Upload, download, and manage files in Google Drive
- **Customer Document Management**: Organize customer documents in structured folders
- **Collaboration Features**: Share files and create shared links
- **Search & Organization**: Search files and organize them by type
- **Customer Support Workflow**: Dedicated endpoints for customer support operations

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with the Google Drive API enabled
2. **OAuth 2.0 Credentials**: Download OAuth 2.0 credentials from Google Cloud Console
3. **Python Dependencies**: Install the required packages (already added to requirements.txt)

## Setup Instructions

### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application" as the application type
4. Give it a name (e.g., "MCP Server Google Drive")
5. Download the JSON credentials file
6. Rename it to `credentials.json` and place it in your project root

### 3. Environment Configuration

Set the following environment variables:

```bash
# Google Drive Configuration
GOOGLE_DRIVE_CREDENTIALS_PATH=credentials.json
GOOGLE_DRIVE_TOKEN_PATH=token.json

# JWT Configuration (for authentication)
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API Keys (if using)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 4. First-Time Authentication

When you first run the server and call a Google Drive endpoint, you'll need to authenticate:

1. Start your MCP server
2. Make a request to `/google-drive/authenticate`
3. A browser window will open for Google OAuth authentication
4. Sign in with your Google account and grant permissions
5. The token will be saved for future use

## API Endpoints

### Authentication
- `POST /google-drive/authenticate` - Authenticate with Google Drive

### Basic File Operations
- `POST /google-drive/create-folder` - Create a new folder
- `POST /google-drive/upload-file` - Upload a file
- `POST /google-drive/upload-content` - Upload content directly
- `GET /google-drive/download-file/{file_id}` - Download a file
- `GET /google-drive/list-files` - List files and folders
- `GET /google-drive/search-files` - Search for files
- `DELETE /google-drive/delete-file/{file_id}` - Delete a file

### Sharing & Collaboration
- `POST /google-drive/share-file` - Share a file with a user
- `POST /google-drive/create-shared-link` - Create a shared link

### Customer Support Operations
- `POST /google-drive/create-customer-folder` - Create customer support folder structure
- `POST /google-drive/upload-customer-document` - Upload customer document
- `GET /google-drive/get-customer-documents/{customer_folder_id}` - Get customer documents
- `GET /google-drive/status` - Check service status

## Customer Support Workflow

### 1. Create Customer Folder Structure

When a new customer is onboarded, create a structured folder:

```python
# Create customer folder with subfolders
response = await client.post("/google-drive/create-customer-folder", 
    data={
        "customer_name": "Acme Corporation",
        "customer_email": "support@acme.com"
    }
)

# This creates:
# - Customer Support - Acme Corporation/
#   ├── Documents/
#   ├── Contracts/
#   ├── Support Tickets/
#   └── Communications/
```

### 2. Upload Customer Documents

Upload documents to the appropriate subfolder:

```python
# Upload a contract
with open("contract.pdf", "rb") as f:
    content = base64.b64encode(f.read()).decode()
    
response = await client.post("/google-drive/upload-customer-document",
    data={
        "customer_folder_id": "folder_id_here",
        "document_content": content,
        "document_name": "Service Agreement 2024.pdf",
        "document_type": "contracts"
    }
)
```

### 3. Retrieve Customer Documents

Get all documents for a customer organized by type:

```python
response = await client.get(f"/google-drive/get-customer-documents/{customer_folder_id}")

# Returns:
{
    "documents": [...],
    "contracts": [...],
    "tickets": [...],
    "communications": [...]
}
```

## Security Considerations

### 1. OAuth Scopes

The integration uses the following scopes:
- `https://www.googleapis.com/auth/drive.file` - Access to files created by the app
- `https://www.googleapis.com/auth/drive.readonly` - Read-only access to files
- `https://www.googleapis.com/auth/drive.metadata.readonly` - Read metadata only

### 2. Token Storage

- OAuth tokens are stored locally in `token.json`
- Tokens are automatically refreshed when expired
- Keep the token file secure and don't commit it to version control

### 3. File Permissions

- Files are created with appropriate permissions
- Sharing is controlled through explicit API calls
- Customer folders are organized to prevent unauthorized access

## Error Handling

The service includes comprehensive error handling:

- **Authentication Errors**: Clear messages when OAuth fails
- **File Operation Errors**: Specific error messages for file operations
- **Permission Errors**: Handles cases where files can't be accessed
- **Network Errors**: Retry logic for transient failures

## Usage Examples

### Basic File Upload

```python
import requests
import base64

# Upload a text file
content = "Hello, this is a test document"
encoded_content = base64.b64encode(content.encode()).decode()

response = requests.post(
    "http://localhost:8000/google-drive/upload-content",
    data={
        "content": encoded_content,
        "file_name": "test_document.txt",
        "mime_type": "text/plain"
    },
    headers={"Authorization": "Bearer your-jwt-token"}
)
```

### Customer Document Management

```python
# Create customer folder
customer_response = requests.post(
    "http://localhost:8000/google-drive/create-customer-folder",
    data={
        "customer_name": "John Doe",
        "customer_email": "john@example.com"
    },
    headers={"Authorization": "Bearer your-jwt-token"}
)

customer_folder_id = customer_response.json()["customer_folder"]["id"]

# Upload support ticket
ticket_content = "Customer reported login issues..."
encoded_ticket = base64.b64encode(ticket_content.encode()).decode()

requests.post(
    "http://localhost:8000/google-drive/upload-customer-document",
    data={
        "customer_folder_id": customer_folder_id,
        "document_content": encoded_ticket,
        "document_name": "Support Ticket #12345.txt",
        "document_type": "tickets"
    },
    headers={"Authorization": "Bearer your-jwt-token"}
)
```

## Troubleshooting

### Common Issues

1. **"Credentials file not found"**
   - Ensure `credentials.json` is in the project root
   - Check the `GOOGLE_DRIVE_CREDENTIALS_PATH` environment variable

2. **"Authentication failed"**
   - Delete `token.json` and re-authenticate
   - Check that the Google Drive API is enabled
   - Verify OAuth credentials are correct

3. **"Permission denied"**
   - Check file permissions in Google Drive
   - Ensure the authenticated user has access to the file/folder

4. **"File not found"**
   - Verify the file ID is correct
   - Check if the file has been moved or deleted

### Debug Mode

Enable debug mode to get more detailed error messages:

```bash
export DEBUG=true
```

## Integration with MCP

The Google Drive integration is fully integrated with your MCP server:

- All endpoints are available as MCP tools
- Authentication is handled through JWT tokens
- Responses are structured for MCP compatibility
- Error handling follows MCP standards

## Next Steps

1. **Test the Integration**: Use the provided examples to test basic functionality
2. **Customize Workflows**: Adapt the customer support workflow to your needs
3. **Add Monitoring**: Implement logging and monitoring for production use
4. **Scale Up**: Consider implementing batch operations for large file sets
5. **Security Review**: Conduct a security review before production deployment 
# FastAPI + JWT + MCP Example with Google Drive Integration

A comprehensive MCP (Model Context Protocol) server with JWT authentication, LLM integration, and Google Drive capabilities for customer support operations.

## Features

- **JWT Authentication**: Secure token-based authentication
- **LLM Integration**: Support for OpenAI and Anthropic models
- **Google Drive Integration**: Complete file management and customer support workflows
- **MCP Protocol**: Full Model Context Protocol implementation
- **Customer Support Tools**: Dedicated endpoints for customer document management

## Install

```bash
pip install -r requirements.txt
```

## Setup

### 1. Environment Variables

Create a `.env` file or set environment variables:

```bash
# JWT Configuration
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API Keys (optional)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Google Drive Configuration
GOOGLE_DRIVE_CREDENTIALS_PATH=credentials.json
GOOGLE_DRIVE_TOKEN_PATH=token.json
```

### 2. Google Drive Setup

1. Follow the detailed setup guide in [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md)
2. Download OAuth credentials from Google Cloud Console
3. Place `credentials.json` in your project root

## Run

```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication
- `POST /register` – JSON {username, password}
- `POST /login` – form-data credentials → returns JWT
- `GET /protected` – requires Authorization: Bearer <token>

### LLM Integration
- `POST /chat` – Send messages to LLM models (OpenAI/Anthropic)

### Google Drive Operations
- `POST /google-drive/authenticate` – Authenticate with Google Drive
- `POST /google-drive/create-folder` – Create folders
- `POST /google-drive/upload-file` – Upload files
- `GET /google-drive/list-files` – List files and folders
- `GET /google-drive/search-files` – Search for files
- `POST /google-drive/create-customer-folder` – Create customer support structure
- `POST /google-drive/upload-customer-document` – Upload customer documents
- `GET /google-drive/get-customer-documents/{id}` – Retrieve customer documents
- `POST /google-drive/share-file` – Share files with users
- `POST /google-drive/create-shared-link` – Create shared links

### MCP Tools
- MCP tools available at `/mcp` – protected via JWT authentication
- All Google Drive operations available as MCP tools

## Customer Support Workflow

The Google Drive integration provides a complete customer support workflow:

1. **Customer Onboarding**: Create structured folders for each customer
2. **Document Management**: Organize documents by type (contracts, tickets, communications)
3. **Collaboration**: Share files and create shared links
4. **Search & Retrieval**: Find and access customer documents quickly

## Testing

Run the integration test:

```bash
python test_google_drive.py
```

Make sure to update the `JWT_TOKEN` variable in the test script with a valid token.

## Documentation

- [Google Drive Setup Guide](GOOGLE_DRIVE_SETUP.md) - Detailed setup instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server is running)

## Security

- JWT tokens for authentication
- OAuth 2.0 for Google Drive access
- Secure file permissions and sharing controls
- Environment variable configuration for sensitive data

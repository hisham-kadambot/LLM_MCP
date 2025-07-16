# Database Setup Guide

This application now uses SQLite database for storing user data and API keys instead of in-memory storage.

## Features

- **User Management**: Store user accounts with hashed passwords
- **API Key Storage**: Securely store API keys per user and model
- **Persistent Data**: Data persists between application restarts
- **Password Security**: Passwords are hashed using bcrypt

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Optional email address
- `hashed_password`: Bcrypt hashed password
- `is_active`: User status (1 = active, 0 = inactive)
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp

### User API Keys Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `model_name`: Name of the LLM model
- `api_key`: Encrypted API key
- `created_at`: Key creation timestamp
- `updated_at`: Last update timestamp

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

Run the database initialization script:

```bash
python init_db.py
```

This will:
- Create the SQLite database file (`app.db`)
- Create all necessary tables
- Create a default admin user (username: `admin`, password: `admin123`)

### 3. Start the Application

```bash
python -m app.main
```

## API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /login` - Login and get access token
- `GET /me` - Get current user information

### API Key Management
- `POST /set_api_key` - Set API key for a model
- `GET /api_keys` - Get all API keys for current user
- `DELETE /api_keys/{model_name}` - Delete API key for a model

### Protected Routes
- `GET /protected` - Test protected endpoint

## Usage Examples

### Register a New User
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=secure_password123"
```

### Set API Key
```bash
curl -X POST "http://localhost:8000/set_api_key" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "openai",
    "api_key": "sk-your-openai-api-key"
  }'
```

### Get User API Keys
```bash
curl -X GET "http://localhost:8000/api_keys" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Security Notes

1. **Change Default Credentials**: After first setup, change the default admin credentials
2. **Environment Variables**: Use environment variables for sensitive configuration
3. **Database File**: The `app.db` file contains sensitive data - keep it secure
4. **Backup**: Regularly backup the database file

## Database Location

The SQLite database file (`app.db`) is created in the root directory of your application.

## Migration from In-Memory Storage

If you were previously using the in-memory storage:
1. Your existing data will not be automatically migrated
2. You'll need to re-register users and re-set API keys
3. The new system provides better security and persistence

## Troubleshooting

### Database Connection Issues
- Ensure the application has write permissions in the directory
- Check that SQLite is properly installed
- Verify the database file path is correct

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that the `app` directory is in your Python path

### Permission Errors
- Ensure the application has read/write permissions for the database file
- On Windows, run as administrator if needed 
from fastapi import APIRouter, Depends
from ..auth import verify_jwt_token, user_api_keys
from ..models import ApiKeyRequest

router = APIRouter()

@router.get("/protected")
def protected(username: str = Depends(verify_jwt_token)):
    return {"msg": f"Hello, {username}! This is protected."}

@router.post("/set_api_key")
def set_api_key(
    api_key_request: ApiKeyRequest,
    username: str = Depends(verify_jwt_token)
):
    # Initialize user's API keys dict if it doesn't exist
    if username not in user_api_keys:
        user_api_keys[username] = {}
    
    # Save the API key for the specified model
    user_api_keys[username][api_key_request.model_name] = api_key_request.api_key
    
    return {
        "msg": f"API key for model '{api_key_request.model_name}' saved successfully for user '{username}'"
    }

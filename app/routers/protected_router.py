from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..auth import verify_jwt_token, get_user_by_username, create_or_update_api_key, get_user_api_keys, delete_api_key
from ..database import get_db
from ..models import ApiKeyRequest, ApiKeyResponse

router = APIRouter()

@router.get("/protected")
def protected(username: str = Depends(verify_jwt_token)):
    return {"msg": f"Hello, {username}! This is protected."}

@router.post("/set_api_key", response_model=ApiKeyResponse)
def set_api_key(
    api_key_request: ApiKeyRequest,
    username: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db)
):
    """Set API key for a specific model"""
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Save the API key to database
    api_key = create_or_update_api_key(
        db=db,
        user_id=user.id,
        model_name=api_key_request.model_name,
        api_key=api_key_request.api_key
    )
    
    return ApiKeyResponse(
        id=api_key.id,
        model_name=api_key.model_name,
        created_at=api_key.created_at
    )

@router.get("/api_keys", response_model=list[ApiKeyResponse])
def get_api_keys(
    username: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db)
):
    """Get all API keys for the current user"""
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    api_keys = get_user_api_keys(db, user.id)
    return [
        ApiKeyResponse(
            id=key.id,
            model_name=key.model_name,
            created_at=key.created_at
        )
        for key in api_keys
    ]

@router.delete("/api_keys/{model_name}")
def delete_api_key_endpoint(
    model_name: str,
    username: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db)
):
    """Delete API key for a specific model"""
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = delete_api_key(db, user.id, model_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key for model '{model_name}' not found"
        )
    
    return {"msg": f"API key for model '{model_name}' deleted successfully"}

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Request Models
class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class ApiKeyRequest(BaseModel):
    model_name: str
    api_key: str

class LLMParaphraseRequest(BaseModel):
    text: str
    model_name: str = "llama2"

class LLMParaphraseResponse(BaseModel):
    paraphrased_text: str

# Response Models
class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ApiKeyResponse(BaseModel):
    id: int
    model_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

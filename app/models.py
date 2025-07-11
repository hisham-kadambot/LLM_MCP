from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str

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

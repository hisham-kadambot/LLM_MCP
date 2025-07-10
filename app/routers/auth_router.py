from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from ..auth import fake_users_db, create_access_token
from ..models import User, TokenResponse

router = APIRouter()

@router.post("/register", status_code=201)
def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(400, "Username already exists")
    fake_users_db[user.username] = user.password
    return {"msg": "User registered"}

@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):
    pwd = fake_users_db.get(form.username)
    if pwd is None or pwd != form.password:
        raise HTTPException(400, "Invalid credentials")
    token = create_access_token(subject=form.username)
    return {"access_token": token, "token_type": "bearer"}

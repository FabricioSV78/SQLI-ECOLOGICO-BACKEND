from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.services import auth_service, db_service
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

class UserRegister(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(user: UserRegister, db: Session = Depends(db_service.get_db)):
    """
    Registrar nuevo usuario.
    """
    user = auth_service.register_user(db, user.email, user.password)
    return {"status": "ok", "user": user.email}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db_service.get_db)):
    """
    Autenticar usuario y devolver JWT.
    """
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
    token = auth_service.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


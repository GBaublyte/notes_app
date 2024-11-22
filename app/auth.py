from datetime import timedelta, datetime

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from jose import JWTError
from sqlalchemy.orm import Session
from app import crud
from app.crud import pwd_context
from app.database import User

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user


def fake_hash_password(password: str):
    return "fakehashed" + password


def fake_verify_password(plain_password: str, hashed_password: str):
    return fake_hash_password(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    print(f"Token: {token}")  # Debugging line
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = request.state.db.query(User).filter(User.username == username).first()
        if user is None:
            return None
        return user
    except JWTError:
        print(f"JWT error: {str(e)}")  # Debugging line
        return None
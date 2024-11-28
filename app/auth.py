from datetime import datetime, timezone
from datetime import timedelta
import logging

from fastapi import Depends, HTTPException, Cookie
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status

from app.database import get_db, User
from app.schemas import TokenData

SECRET_KEY = "132b159e356b9187054c4b5ec2f82b4f42e11b52f62a0818f57ff023d626db59"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
    datefmt='%Y-%m-%d %H:%M:%S',  # Date format
)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if access_token is None:
        logger.error("Access token is None")
        raise credentials_exception
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error("Username is None in token payload")
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        logger.error("The token is not valid")
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        logger.error("User not found in database")
        raise credentials_exception
    return user

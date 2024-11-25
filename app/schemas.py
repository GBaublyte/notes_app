from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class UserInDB(UserBase):
    hashed_password: str


class LoginUser(BaseModel):
    username: str
    password: str

class CategoryBase(BaseModel):
    title: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class NoteBase(BaseModel):
    note_name: str
    description: str
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class NoteCreate(BaseModel):
    note_name: str
    description: str


class NoteUpdate(NoteBase):
    pass


class Note(NoteCreate):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

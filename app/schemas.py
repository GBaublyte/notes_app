from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserCreate(BaseModel):
    email: str
    password: str


class User(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True


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
    title: str
    content: str
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


class Note(NoteBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True
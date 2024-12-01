from typing import Optional
from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    id: int
    username: str

    class Config(ConfigDict):
        from_attributes = True


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

    class Config(ConfigDict):
        from_attributes = True

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

    class Config(ConfigDict):
        from_attributes = True

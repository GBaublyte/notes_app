from pydantic import BaseModel
from datetime import date


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    username: str
    password: str


class NoteBase(BaseModel):
    note_name: str
    description: str
    to_be_done_by: date


class NoteResponse(BaseModel):
    id: int
    note_name: str
    description: str
    to_be_done_by: date
    status: str
    owner_id: int

    class Config:
        from_attributes = True


class StatusChange(BaseModel):
    id: int
    note_name: str
    status: str

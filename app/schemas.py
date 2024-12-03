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

from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str
    username: str = None
    full_name: str = None

class UserLogin(BaseModel):
    email: str
    password: str
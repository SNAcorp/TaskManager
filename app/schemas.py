from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from typing import List


class IsServerOnline(BaseModel):
    terminal_id: int
    token: str


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    phone_number: str


class UserCreate(UserBase):
    password: str
    confirm_password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserInDBBase(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    is_verified: bool
    role: str
    registration_date: datetime
    block_date: Optional[datetime] = None

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


class SubtaskCreate(BaseModel):
    name: str

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    deadline: datetime
    subtasks: List[SubtaskCreate]

class SubtaskUpdate(BaseModel):
    is_completed: bool

class TaskUpdate(BaseModel):
    is_completed: bool
    subtasks: List[SubtaskUpdate]
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    tenant_id: Optional[str]
    created_at: datetime


class TransactionCreate(BaseModel):
    amount: float
    category: Optional[str] = None
    note: Optional[str] = None


class TransactionOut(TransactionCreate):
    id: str
    tenant_id: str
    user_id: Optional[str]
    created_at: datetime
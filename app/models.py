from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import uuid
from datetime import datetime


class Tenant(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default=None, primary_key=True)
    name: str
    domain: Optional[str] = None
    users: List['User'] = Relationship(back_populates='tenant')


class User(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    hashed_password: str
    tenant_id: Optional[uuid.UUID] = Field(default=None, foreign_key='tenant.id')
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tenant: Optional[Tenant] = Relationship(back_populates='users')


class Transaction(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default=None, primary_key=True)
    tenant_id: uuid.UUID = Field(foreign_key='tenant.id')
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key='user.id')
    amount: float
    category: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
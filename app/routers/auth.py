from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app import models, schemas, security
from app.database import get_session
from datetime import timedelta


router = APIRouter()


@router.post('/signup', response_model=schemas.UserOut)
def signup(user_in: schemas.UserCreate, tenant: str | None = None, session: Session = Depends(get_session)):
    # tenant param optional - if provided, associate user to tenant
    # Check existing user
    query = select(models.User).where(models.User.email == user_in.email)
    existing_user = session.exec(query).first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    
    hashed_password = security.get_password_hash(user_in.password)
    user = models.User(email=user_in.email, hashed_password=hashed_password)
    
    # If tenant domain string provided, try to find tenant and set tenant_id
    if tenant:
        tenant_query = session.exec(select(models.Tenant).where(models.Tenant.domain == tenant)).first()
        if not tenant_query:
            raise HTTPException(status_code=404, detail='Tenant not found')
        user.tenant_id = tenant_query.id
    
    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f'Failed to create user: {str(e)}')
    
    return schemas.UserOut(
        id=str(user.id), 
        email=user.email, 
        tenant_id=str(user.tenant_id) if user.tenant_id else None, 
        created_at=user.created_at
    )


@router.post('/login', response_model=schemas.Token)
def login(form_data: schemas.UserCreate, session: Session = Depends(get_session)):
    query = select(models.User).where(models.User.email == form_data.email)
    user = session.exec(query).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    
    token_data = {"user_id": str(user.id)}
    if user.tenant_id:
        token_data['tenant_id'] = str(user.tenant_id)
    
    access_token = security.create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}
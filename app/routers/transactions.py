from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from typing import List, Optional
from app import models, schemas, security
from app.database import get_session


router = APIRouter()


# Dependency: get current user from Authorization header
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_scheme), session: Session = Depends(get_session)):
    token = credentials.credentials
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(401, 'Invalid token')
    
    user_id = payload.get('user_id')
    query = select(models.User).where(models.User.id == user_id)
    user = session.exec(query).first()
    if not user:
        raise HTTPException(401, 'User not found')
    return user


@router.post('/', response_model=schemas.TransactionOut)
def create_transaction(tx_in: schemas.TransactionCreate, current_user: models.User = Depends(get_current_user), session: Session = Depends(get_session)):
    if not current_user.tenant_id:
        raise HTTPException(400, 'User has no tenant')
    
    try:
        transaction = models.Transaction(
            tenant_id=current_user.tenant_id, 
            user_id=current_user.id, 
            amount=tx_in.amount, 
            category=tx_in.category, 
            note=tx_in.note
        )
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return transaction
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f'Failed to create transaction: {str(e)}')


@router.get('/', response_model=List[schemas.TransactionOut])
def list_transactions(current_user: models.User = Depends(get_current_user), session: Session = Depends(get_session)):
    if not current_user.tenant_id:
        raise HTTPException(400, 'User has no tenant')
    
    query = select(models.Transaction).where(models.Transaction.tenant_id == current_user.tenant_id)
    transactions = session.exec(query).all()
    return transactions
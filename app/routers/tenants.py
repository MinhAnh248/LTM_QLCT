from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app import models, schemas
from app.database import get_session
import uuid


router = APIRouter()


@router.post('/')
def create_tenant(name: str, domain: str, session: Session = Depends(get_session)):
    try:
        tenant = models.Tenant(name=name, domain=domain)
        session.add(tenant)
        session.commit()
        session.refresh(tenant)
        return {"id": str(tenant.id), "name": tenant.name, "domain": tenant.domain}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f'Failed to create tenant: {str(e)}')


@router.get('/by-domain')
def get_tenant_by_domain(domain: str, session: Session = Depends(get_session)):
    try:
        query = select(models.Tenant).where(models.Tenant.domain == domain)
        tenant = session.exec(query).first()
        if not tenant:
            raise HTTPException(404, 'Tenant not found')
        return {"id": str(tenant.id), "name": tenant.name, "domain": tenant.domain}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')
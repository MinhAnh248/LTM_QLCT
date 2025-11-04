from fastapi import FastAPI
from app.routers import auth, tenants, transactions
from app.database import engine, get_session
from app import models

models.SQLModel.metadata.create_all(bind=engine)

app = FastAPI(title='Expense Manager (Multi-tenant)')
app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(tenants.router, prefix='/tenants', tags=['tenants'])
app.include_router(transactions.router, prefix='/transactions', tags=['transactions'])


@app.get('/')
def root():
    return {"status": "ok", "message": "Expense Manager API"}
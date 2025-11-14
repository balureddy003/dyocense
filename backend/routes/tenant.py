"""
Tenant Management Routes

Create and list tenants. In production, listing should be admin-only.
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import DBSession
from backend.models.tenant import Tenant
from backend.schemas.tenant import TenantCreate, TenantOut

router = APIRouter()


@router.get("/", response_model=List[TenantOut])
async def list_tenants(db: DBSession) -> List[TenantOut]:
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = result.scalars().all()
    return [TenantOut.model_validate(t) for t in tenants]


@router.post("/", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
async def create_tenant(payload: TenantCreate, db: DBSession) -> TenantOut:
    tenant = Tenant(name=payload.name)
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return TenantOut.model_validate(tenant)


@router.get("/{tenant_id}", response_model=TenantOut)
async def get_tenant(tenant_id: str, db: DBSession) -> TenantOut:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return TenantOut.model_validate(tenant)

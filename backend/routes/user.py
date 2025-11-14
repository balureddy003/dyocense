"""
User Management Routes

Tenant-scoped user CRUD and self endpoint. RBAC to be added later.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import DBSession, get_current_user
from backend.models.user import User
from backend.schemas.user import UserCreate, UserOut

router = APIRouter()


@router.get("/", response_model=List[UserOut])
async def list_users(db: DBSession, current_user: dict = Depends(get_current_user)) -> List[UserOut]:
    tenant_id = current_user["tenant_id"]
    result = await db.execute(select(User).where(User.tenant_id == tenant_id).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [UserOut.model_validate(u) for u in users]


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: DBSession, current_user: dict = Depends(get_current_user)) -> UserOut:
    from backend.utils.auth import hash_password
    
    tenant_id = current_user["tenant_id"]
    user = User(
        tenant_id=tenant_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/me", response_model=UserOut)
async def get_me(db: DBSession, current_user: dict = Depends(get_current_user)) -> UserOut:
    # Look up the current user by email (sub) and tenant_id
    result = await db.execute(
        select(User).where(User.tenant_id == current_user["tenant_id"], User.email == current_user["email"]) 
    )
    user = result.scalar_one_or_none()
    if not user:
        # If not found, synthesize a lightweight record (not persisted) to satisfy UI needs during early dev
        fake = UserOut(
            id="00000000-0000-0000-0000-000000000000",
            tenant_id=current_user["tenant_id"],
            email=current_user["email"],
            role=current_user.get("role", "user"),
            is_active=True,
            created_at=None,  # type: ignore[arg-type]
        )
        return fake
    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, db: DBSession, current_user: dict = Depends(get_current_user)) -> UserOut:
    result = await db.execute(select(User).where(User.id == user_id, User.tenant_id == current_user["tenant_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: DBSession, current_user: dict = Depends(get_current_user)) -> None:
    await db.execute(delete(User).where(User.id == user_id, User.tenant_id == current_user["tenant_id"]))
    # Commit handled by dependency; return 204
    return None

"""
Workspace Routes

Tenant-scoped workspaces with basic CRUD for UI needs.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, delete

from backend.dependencies import DBSession, get_current_user
from backend.models.workspace import Workspace
from backend.schemas.workspace import WorkspaceCreate, WorkspaceOut

router = APIRouter()


@router.get("/", response_model=List[WorkspaceOut])
async def list_workspaces(db: DBSession, current_user: dict = Depends(get_current_user)) -> List[WorkspaceOut]:
    tenant_id = current_user["tenant_id"]
    result = await db.execute(select(Workspace).where(Workspace.tenant_id == tenant_id).order_by(Workspace.created_at.desc()))
    workspaces = result.scalars().all()
    return [WorkspaceOut.model_validate(w) for w in workspaces]


@router.post("/", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
async def create_workspace(payload: WorkspaceCreate, db: DBSession, current_user: dict = Depends(get_current_user)) -> WorkspaceOut:
    w = Workspace(tenant_id=current_user["tenant_id"], name=payload.name, description=payload.description)
    db.add(w)
    await db.flush()
    await db.refresh(w)
    return WorkspaceOut.model_validate(w)


@router.get("/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(workspace_id: str, db: DBSession, current_user: dict = Depends(get_current_user)) -> WorkspaceOut:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id, Workspace.tenant_id == current_user["tenant_id"]))
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return WorkspaceOut.model_validate(w)


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace(workspace_id: str, payload: WorkspaceCreate, db: DBSession, current_user: dict = Depends(get_current_user)) -> WorkspaceOut:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id, Workspace.tenant_id == current_user["tenant_id"]))
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if payload.name:
        w.name = payload.name
    w.description = payload.description
    await db.flush()
    await db.refresh(w)
    return WorkspaceOut.model_validate(w)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(workspace_id: str, db: DBSession, current_user: dict = Depends(get_current_user)) -> None:
    await db.execute(delete(Workspace).where(Workspace.id == workspace_id, Workspace.tenant_id == current_user["tenant_id"]))
    return None

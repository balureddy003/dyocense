from __future__ import annotations

import uuid
from importlib import resources
import json
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import jsonschema

# Load shared schemas
plan_schema = json.loads(resources.files("packages.contracts.schemas").joinpath("plan.schema.json").read_text(encoding="utf-8"))
workspace_schema = json.loads(resources.files("packages.contracts.schemas").joinpath("workspace.schema.json").read_text(encoding="utf-8"))


def _sample_plan(title: str) -> Dict:
    return {
        "id": f"plan-{uuid.uuid4().hex[:8]}",
        "title": title,
        "summary": "Dyocense generated getting-started plan.",
        "created_at": "",
        "updated_at": "",
        "tasks": [
            {"label": "Define MVP scope", "owner": "Founder", "status": "In progress"},
            {"label": "Assign owners", "owner": "Ops lead", "status": "Not started"},
            {"label": "Launch pilot", "owner": "CX lead", "status": "Not started"},
        ],
    }


def _sample_workspace(name: str) -> Dict:
    return {
        "id": f"ws-{uuid.uuid4().hex[:8]}",
        "name": name,
        "industry": "general_smb",
        "region": "na",
        "created_at": "",
        "updated_at": "",
    }


TENANT_PLANS: Dict[str, List[Dict]] = {}
TENANT_WORKSPACES: Dict[str, Dict] = {}


class OnboardingRequest(BaseModel):
    workspace_name: str = Field(default="Sample Workspace")
    plan_title: str = Field(default="Sample Launch Plan")
    archetype_id: str | None = Field(default=None, description="Template used to seed the plan.")


app = FastAPI(
    title="SMB Gateway",
    version="0.1.0",
    description="Stubbed onboarding + plan endpoints consumed by the SMB UI.",
)


def _store_plan(tenant_id: str, plan: Dict) -> None:
    TENANT_PLANS.setdefault(tenant_id, [])
    existing = TENANT_PLANS[tenant_id]
    # Keep latest at front
    existing.insert(0, plan)
    TENANT_PLANS[tenant_id] = existing[:10]


@app.post("/v1/onboarding/{tenant_id}")
def run_onboarding(tenant_id: str, body: OnboardingRequest):
    workspace = _sample_workspace(body.workspace_name)
    plan = _sample_plan(body.plan_title)

    try:
        jsonschema.validate(instance=workspace, schema=workspace_schema)
        jsonschema.validate(instance=plan, schema=plan_schema)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=500, detail=f"Schema validation failed: {exc.message}") from exc

    TENANT_WORKSPACES[tenant_id] = workspace
    _store_plan(tenant_id, plan)

    return {"workspace": workspace, "plan": plan}


@app.get("/v1/tenants/{tenant_id}/plans")
def list_plans(tenant_id: str, limit: int = Query(default=5, ge=1, le=20)):
    items = TENANT_PLANS.get(tenant_id)
    if not items:
        # generate default sample if onboarding not run
        plan = _sample_plan("Sample Launch Plan")
        jsonschema.validate(instance=plan, schema=plan_schema)
        TENANT_PLANS[tenant_id] = [plan]
        items = TENANT_PLANS[tenant_id]
    return {"items": items[:limit], "count": len(items)}

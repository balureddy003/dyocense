from fastapi import FastAPI, Depends, Body
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid
import time

from agent_logic import run_agent_conversation
from packages.kernel_common.logging import configure_logging

# Simple in-memory stores for dev/demo. Replace with DB in production.
USERS: Dict[str, Dict] = {}
TENANTS: Dict[str, Dict] = {}
WORKSPACES: Dict[str, Dict] = {}
VERIFICATION_TOKENS: Dict[str, Dict] = {}

logger = configure_logging("agent-shell")

app = FastAPI(title="Agent Shell API", description="APIs for conversational UI shell, agent flows, and workspace/tenant context.")

# Models
class MessageRequest(BaseModel):
    tenant_id: str
    workspace_id: str
    user_id: str
    message: str
    context: Optional[Dict] = None

class MessageResponse(BaseModel):
    reply: str
    actions: Optional[List[Dict]] = None
    context: Optional[Dict] = None

class WorkspaceInfo(BaseModel):
    tenant_id: str
    workspace_id: str
    name: str
    members: List[str]
    metadata: Optional[Dict] = None

# Endpoints
@app.post("/v1/agent/message", response_model=MessageResponse)
def agent_message(payload: MessageRequest = Body(...)):
    # Use actual LangChain agent logic for real response
    logger.debug("agent_message invoked for tenant=%s workspace=%s", payload.tenant_id, payload.workspace_id)
    agent_reply = run_agent_conversation(payload.message, context={"tenant_id": payload.tenant_id, "workspace_id": payload.workspace_id, **(payload.context or {})})
    # Example: parse agent_reply for actionable triggers (demo only)
    actions = [
        {"type": "card", "label": "View Analytics", "description": "Open workspace analytics dashboard.", "action": "analytics", "payload": {"workspace_id": payload.workspace_id}},
        {"type": "card", "label": "Start Workflow", "description": "Trigger a workflow for this workspace.", "action": "workflow", "payload": {"tenant_id": payload.tenant_id}},
        {"type": "card", "label": "Calculator", "description": "Perform a calculation.", "action": "calculator", "payload": {"expression": "2+2"}},
    ]
    return MessageResponse(
        reply=agent_reply,
        actions=actions,
        context={"tenant_id": payload.tenant_id, "workspace_id": payload.workspace_id}
    )

@app.get("/v1/workspace/{tenant_id}/{workspace_id}", response_model=WorkspaceInfo)
def get_workspace(tenant_id: str, workspace_id: str):
    # TODO: Fetch workspace info from DB
    logger.debug("get_workspace request for tenant=%s workspace=%s", tenant_id, workspace_id)
    return WorkspaceInfo(
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        name="Demo Workspace",
        members=["user1", "user2"],
        metadata={"sample": True}
    )

# Health check
@app.get("/health")
def health():
    return {"status": "ok", "service": "agent_shell"}


# --- Simple Auth / Signup / Verify (dev/demo) ---
class SignupRequest(BaseModel):
    email: str
    name: Optional[str] = None
    company: Optional[str] = None


class SignupResponse(BaseModel):
    user_id: str
    tenant_id: str
    workspace_id: str
    verification_token: str


@app.post("/v1/auth/signup", response_model=SignupResponse)
def signup(payload: SignupRequest = Body(...)):
    # Create user
    logger.info("Signup requested for email=%s", payload.email)
    user_id = f"u_{uuid.uuid4().hex[:8]}"
    USERS[user_id] = {"id": user_id, "email": payload.email, "name": payload.name, "status": "pending", "created_at": int(time.time())}

    # Create tenant and default workspace
    tenant_id = f"t_{uuid.uuid4().hex[:8]}"
    TENANTS[tenant_id] = {"id": tenant_id, "name": payload.company or "Demo Tenant", "owner_user_id": user_id, "plan": "trial", "created_at": int(time.time())}
    workspace_id = f"w_{uuid.uuid4().hex[:8]}"
    WORKSPACES[workspace_id] = {"id": workspace_id, "tenant_id": tenant_id, "name": "Default Workspace", "created_at": int(time.time())}

    # Create verification token (dev: return token in response so tests can use it)
    token = uuid.uuid4().hex
    VERIFICATION_TOKENS[token] = {"user_id": user_id, "expires_at": int(time.time()) + 60 * 60}

    # In production: send email with verification link. For dev, return token in payload.
    return SignupResponse(user_id=user_id, tenant_id=tenant_id, workspace_id=workspace_id, verification_token=token)


class VerifyRequest(BaseModel):
    token: str


class VerifyResponse(BaseModel):
    user_id: str
    tenant_id: str
    workspace_id: str
    jwt: str


@app.post("/v1/auth/verify", response_model=VerifyResponse)
def verify(payload: VerifyRequest = Body(...)):
    logger.info("Verification attempt for token=%s", payload.token)
    info = VERIFICATION_TOKENS.get(payload.token)
    if not info:
        return VerifyResponse(user_id="", tenant_id="", workspace_id="", jwt="")
    if info["expires_at"] < int(time.time()):
        VERIFICATION_TOKENS.pop(payload.token, None)
        return VerifyResponse(user_id="", tenant_id="", workspace_id="", jwt="")

    user_id = info["user_id"]
    # Activate user
    USERS[user_id]["status"] = "active"

    # Find tenant/workspace for this demo user
    tenant = next((t for t in TENANTS.values() if t["owner_user_id"] == user_id), None)
    workspace = next((w for w in WORKSPACES.values() if w["tenant_id"] == (tenant and tenant["id"])), None)

    # Simple JWT placeholder for dev
    jwt = f"dev-jwt-{user_id}"
    tenant_id = tenant["id"] if tenant else ""
    workspace_id = workspace["id"] if workspace else ""

    return VerifyResponse(user_id=user_id, tenant_id=tenant_id, workspace_id=workspace_id, jwt=jwt)

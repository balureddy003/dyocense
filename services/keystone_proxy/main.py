from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import httpx
import os

from packages.kernel_common.logging import configure_logging
logger = configure_logging("keystone-proxy")
app = FastAPI(title="Keystone Proxy API")

# Config via env
KEYSTONE_GRAPHQL = os.getenv("KEYSTONE_GRAPHQL", "http://localhost:3001/api/graphql")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")

def require_api_key(x_api_key: str | None = Header(None)):
    """Dependency that enforces a proxy API key when PROXY_API_KEY is set in env."""
    if PROXY_API_KEY:
        if not x_api_key or x_api_key != PROXY_API_KEY:
            logger.warning("Unauthorized request, missing or invalid x-api-key header")
            raise HTTPException(status_code=401, detail="Unauthorized")
    return True


class OnboardingRequest(BaseModel):
    workspace_name: str = "Sample Workspace"
    plan_title: str = "Sample Launch Plan"
    tasks: list[str] = ["Define MVP", "Assign owners", "Launch"]


async def run_graphql(query: str, variables: dict | None = None):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(KEYSTONE_GRAPHQL, json={"query": query, "variables": variables}, timeout=10.0)
        except httpx.RequestError as e:
            logger.exception("GraphQL request failed")
            raise HTTPException(status_code=502, detail="Unable to reach Keystone GraphQL")

        if resp.status_code != 200:
            logger.error("Keystone returned status %s: %s", resp.status_code, resp.text)
            raise HTTPException(status_code=502, detail="Keystone GraphQL error")
        body = resp.json()
        if body.get("errors"):
            logger.error("GraphQL errors: %s", body.get("errors"))
            raise HTTPException(status_code=400, detail=body.get("errors"))
        return body.get("data")


@app.post("/v1/onboarding/{tenant_name}")
async def create_onboarding(tenant_name: str, req: OnboardingRequest, _ok: bool = Depends(require_api_key)):
    # Create tenant
    create_tenant_q = '''mutation CreateTenant($name: String!) { createTenant(data: { name: $name }) { id name } }'''
    try:
        tenant_data = await run_graphql(create_tenant_q, {"name": tenant_name})
    except HTTPException as e:
        # If tenant exists, try to query it
        # fallthrough to get tenant by name
        tenant_data = None

    if not tenant_data or not tenant_data.get("createTenant"):
        # Query tenant by name
        query = '''query ($name: String) { tenants(where: { name: $name }) { id name } }'''
        data = await run_graphql(query, {"name": tenant_name})
        tenants = data.get("tenants", [])
        if tenants:
            tenant = tenants[0]
        else:
            raise HTTPException(status_code=500, detail="Unable to create or find tenant")
    else:
        tenant = tenant_data.get("createTenant")

    tenant_id = tenant["id"]

    # Create workspace
    create_ws_q = '''mutation CreateWorkspace($name: String!, $tenantId: ID!) { createWorkspace(data: { name: $name, tenant: { connect: { id: $tenantId } } }) { id name } }'''
    ws_data = await run_graphql(create_ws_q, {"name": req.workspace_name, "tenantId": tenant_id})
    workspace = ws_data.get("createWorkspace")
    if not workspace:
        raise HTTPException(status_code=500, detail="Unable to create workspace")

    workspace_id = workspace["id"]

    # Create project/plan
    create_plan_q = '''mutation CreateProject($title: String!, $workspaceId: ID!) { createProject(data: { title: $title, workspace: { connect: { id: $workspaceId } } }) { id title } }'''
    plan_data = await run_graphql(create_plan_q, {"title": req.plan_title, "workspaceId": workspace_id})
    plan = plan_data.get("createProject")
    if not plan:
        raise HTTPException(status_code=500, detail="Unable to create plan")

    # Optionally create tasks as Project description or as separate items; keep simple
    return {"tenant": tenant, "workspace": workspace, "plan": plan}


class VerifyRequest(BaseModel):
    token: str


@app.post("/v1/auth/verify")
async def verify_token(req: VerifyRequest, _ok: bool = Depends(require_api_key)):
    """Simple verify endpoint: for dev tokens create/find a tenant and return a jwt-like token and tenant id.
    This is a dev/proxy implementation. Replace with your real auth in production.
    """
    token = req.token
    if not token:
        raise HTTPException(status_code=400, detail="missing token")

    # For dev tokens that contain 'dev', return a simple dev tenant
    tenant_name = "dev-tenant" if "dev" in token else token

    # Ensure tenant exists (create or find)
    create_tenant_q = '''mutation CreateTenant($name: String!) { createTenant(data: { name: $name }) { id name } }'''
    try:
        tenant_data = await run_graphql(create_tenant_q, {"name": tenant_name})
        tenant = tenant_data.get("createTenant")
    except HTTPException:
        # If creation failed, try to find existing tenant
        query = '''query ($name: String) { tenants(where: { name: $name }) { id name } }'''
        data = await run_graphql(query, {"name": tenant_name})
        tenants = data.get("tenants", [])
        tenant = tenants[0] if tenants else None

    if not tenant:
        raise HTTPException(status_code=500, detail="unable to create/find tenant")

    # Attempt to find a workspace for the tenant
    ws_query = '''query ($tenantId: ID) { workspaces(where: { tenant: { id: $tenantId } }) { id name } }'''
    ws_data = await run_graphql(ws_query, {"tenantId": tenant["id"]})
    workspaces = ws_data.get("workspaces", []) if ws_data else []
    workspace_id = workspaces[0]["id"] if workspaces else None

    # Return a fake jwt and the tenant/workspace ids
    return {"jwt": f"jwt-{tenant['id']}", "tenant_id": tenant["id"], "workspace_id": workspace_id, "user": {"name": tenant.get("name")}}


@app.get("/v1/tenants/{tenant_id}/workspaces")
async def list_workspaces(tenant_id: str, _ok: bool = Depends(require_api_key)):
    query = '''query ($tenantId: ID) { workspaces(where: { tenant: { id: $tenantId } }) { id name createdAt } }'''
    data = await run_graphql(query, {"tenantId": tenant_id})
    return data.get("workspaces", [])


@app.get("/v1/tenants/{tenant_id}/plans")
async def list_plans(tenant_id: str, _ok: bool = Depends(require_api_key)):
    # Query projects related to workspaces under the tenant
    query = '''query ($tenantId: ID) { projects(where: { workspace: { tenant: { id: $tenantId } } }) { id title description status createdAt workspace { id name } } }'''
    data = await run_graphql(query, {"tenantId": tenant_id})
    return data.get("projects", [])

# 🔒 Security & Multi-Tenancy

**Version:** 4.0 (PostgreSQL Row-Level Security)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Multi-Tenancy Architecture](#2-multi-tenancy-architecture)
3. [Row-Level Security (RLS)](#3-row-level-security-rls)
4. [Authentication & Authorization](#4-authentication--authorization)
5. [Data Encryption](#5-data-encryption)
6. [Compliance (GDPR, SOC2)](#6-compliance-gdpr-soc2)
7. [Security Audit](#7-security-audit)

---

## 🎯 1. Overview

### **Security Philosophy**

> **"Security by design, not by afterthought"**

**Key Principles:**

- ✅ **Zero-Trust:** Every request validated (JWT + RLS)
- ✅ **Defense-in-Depth:** Multiple layers (network, app, database, encryption)
- ✅ **Least Privilege:** Users/services only access what they need
- ✅ **Audit Everything:** Every data access logged for forensics

---

### **Multi-Tenancy Model**

| Approach | Data Isolation | Complexity | Cost Efficiency |
|----------|---------------|------------|-----------------|
| **DB per Tenant** | Physical | High | Low (many databases) |
| **Schema per Tenant** | Logical | Medium | Medium |
| **RLS per Tenant** ✅ | Row-Level | Low | **High (single DB)** |

**Why RLS?**

- ✅ **Single Database:** Simplified backups, upgrades
- ✅ **PostgreSQL Native:** Built-in, battle-tested
- ✅ **Cost:** <$1/tenant/month (vs. $5 for separate databases)

---

## 🏢 2. Multi-Tenancy Architecture

### **Tenant Isolation Strategy**

**Every table has `tenant_id` column:**

```sql
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    industry TEXT,  -- e.g., "restaurant", "retail"
    plan TEXT DEFAULT 'basic',  -- "basic", "pro", "enterprise"
    
    -- Subscription
    subscription_status TEXT DEFAULT 'active',  -- "active", "suspended", "canceled"
    mrr NUMERIC DEFAULT 0,  -- Monthly Recurring Revenue
    
    -- Limits (soft caps)
    max_users INT DEFAULT 5,
    max_connectors INT DEFAULT 3,
    max_monthly_queries INT DEFAULT 1000,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tenants_status ON tenants(subscription_status);
```

---

### **User-Tenant Association**

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  -- bcrypt hashed
    
    -- Role-Based Access Control (RBAC)
    role TEXT DEFAULT 'user',  -- "admin", "manager", "user"
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);

-- Ensure email unique per tenant
CREATE UNIQUE INDEX idx_users_email_tenant ON users(tenant_id, email);
```

---

### **RBAC Permissions**

| Role | Permissions |
|------|-------------|
| **Admin** | Full access (manage users, billing, connectors) |
| **Manager** | Read/write data, create goals, view reports |
| **User** | Read-only access to assigned metrics |

```sql
CREATE TABLE permissions (
    permission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role TEXT NOT NULL,
    resource TEXT NOT NULL,  -- e.g., "goals", "connectors", "users"
    action TEXT NOT NULL,    -- "read", "write", "delete"
    
    UNIQUE(role, resource, action)
);

-- Seed permissions
INSERT INTO permissions (role, resource, action) VALUES
    ('admin', '*', '*'),  -- Superuser
    ('manager', 'goals', 'read'),
    ('manager', 'goals', 'write'),
    ('manager', 'metrics', 'read'),
    ('user', 'metrics', 'read');
```

---

## 🔐 3. Row-Level Security (RLS)

### **How RLS Works**

**PostgreSQL RLS:** Automatically filters rows based on session variables

```sql
-- Enable RLS on table
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

-- Create policy: users can only see their tenant's data
CREATE POLICY tenant_isolation_policy ON goals
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Policy for admins (see all tenants)
CREATE POLICY admin_access_policy ON goals
    TO admin_role
    USING (TRUE);
```

---

### **Setting Session Variables**

**In application code (FastAPI middleware):**

```python
from fastapi import Request
from sqlalchemy import text

async def set_tenant_context(request: Request, db: Session):
    """Middleware: Set tenant_id from JWT token"""
    
    # Extract tenant_id from JWT
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = decode_jwt(token)
    tenant_id = payload["tenant_id"]
    
    # Set PostgreSQL session variable
    db.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
    
    return tenant_id
```

---

### **RLS for All Tables**

**Apply to every tenant-scoped table:**

```sql
-- Goals
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON goals
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Metrics
ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON metrics
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Connectors
ALTER TABLE connectors ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON connectors
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Conversations (chat history)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON conversations
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

---

### **Testing RLS**

```python
async def test_rls():
    # Simulate two tenants
    tenant_a = "123e4567-e89b-12d3-a456-426614174000"
    tenant_b = "987fcdeb-51a2-43e7-9c4f-12345678abcd"
    
    # Set tenant A context
    db.execute(text(f"SET app.current_tenant_id = '{tenant_a}'"))
    
    # Query should only return tenant A's goals
    goals_a = db.query(Goal).all()
    assert all(g.tenant_id == tenant_a for g in goals_a)
    
    # Switch to tenant B
    db.execute(text(f"SET app.current_tenant_id = '{tenant_b}'"))
    
    # Should only see tenant B's data
    goals_b = db.query(Goal).all()
    assert all(g.tenant_id == tenant_b for g in goals_b)
    
    print("✅ RLS working correctly!")
```

---

## 🔑 4. Authentication & Authorization

### **Auth Stack**

| Component | Technology |
|-----------|-----------|
| **Auth Protocol** | OAuth2 with Password Grant |
| **Token Format** | JWT (JSON Web Token) |
| **Password Hashing** | bcrypt (10 rounds) |
| **Session Management** | Stateless (JWT only) |
| **MFA (future)** | TOTP (Google Authenticator) |

---

### **JWT Token Structure**

```json
{
  "sub": "user_id_123",
  "tenant_id": "tenant_abc",
  "role": "manager",
  "email": "john@acme.com",
  "exp": 1700000000,
  "iat": 1699996400
}
```

**Token Expiry:**

- Access Token: 1 hour
- Refresh Token: 7 days

---

### **FastAPI Authentication**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

def decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Dependency: Extract user from JWT"""
    payload = decode_jwt(token)
    
    user = db.query(User).filter(User.user_id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Set tenant context for RLS
    db.execute(text(f"SET app.current_tenant_id = '{user.tenant_id}'"))
    
    return user
```

---

### **Login Endpoint**

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check tenant active
    tenant = db.query(Tenant).filter(Tenant.tenant_id == user.tenant_id).first()
    if tenant.subscription_status != "active":
        raise HTTPException(status_code=403, detail="Subscription suspended")
    
    # Generate JWT
    access_token = create_access_token(data={
        "sub": str(user.user_id),
        "tenant_id": str(user.tenant_id),
        "role": user.role,
        "email": user.email
    })
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}
```

---

## 🔐 5. Data Encryption

### **Encryption at Rest**

| Data Type | Encryption Method |
|-----------|------------------|
| **Database** | PostgreSQL Transparent Data Encryption (TDE) |
| **Backups** | AES-256 encrypted backups (pgBackRest) |
| **Secrets** | HashiCorp Vault or AWS Secrets Manager |
| **Env Variables** | `.env` files NOT committed (use `.env.example`) |

**Enable TDE:**

```bash
# PostgreSQL config
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
```

---

### **Encryption in Transit**

**TLS 1.3 everywhere:**

```python
# FastAPI with HTTPS
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=443,
        ssl_keyfile="/etc/ssl/private/key.pem",
        ssl_certfile="/etc/ssl/certs/cert.pem"
    )
```

---

### **Sensitive Data Handling**

**Never log sensitive data:**

```python
import logging

# ❌ BAD
logging.info(f"User password: {password}")

# ✅ GOOD
logging.info(f"User login attempt: {email}")
```

**Redact PII in logs:**

```python
def redact_pii(log_message: str) -> str:
    # Redact email
    log_message = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL_REDACTED]', log_message)
    # Redact credit cards
    log_message = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CC_REDACTED]', log_message)
    return log_message
```

---

## 📜 6. Compliance (GDPR, SOC2)

### **GDPR Requirements**

**1. Right to Access (Data Export)**

```python
@router.get("/gdpr/export")
async def export_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Export all user data (GDPR Article 20)"""
    
    export = {
        "user": {
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat()
        },
        "goals": [g.to_dict() for g in db.query(Goal).filter_by(tenant_id=current_user.tenant_id).all()],
        "metrics": [m.to_dict() for m in db.query(Metric).filter_by(tenant_id=current_user.tenant_id).all()],
        "conversations": [c.to_dict() for c in db.query(Conversation).filter_by(tenant_id=current_user.tenant_id).all()]
    }
    
    return export
```

---

**2. Right to Erasure (Data Deletion)**

```python
@router.delete("/gdpr/delete-account")
async def delete_user_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete all user data (GDPR Article 17)"""
    
    tenant_id = current_user.tenant_id
    
    # Delete all tenant data (cascades via foreign keys)
    db.query(Tenant).filter(Tenant.tenant_id == tenant_id).delete()
    db.commit()
    
    logging.info(f"GDPR deletion: Tenant {tenant_id} deleted")
    
    return {"message": "Account and all data deleted"}
```

---

**3. Data Retention Policy**

```sql
-- Auto-delete old conversation history
CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
    'cleanup-old-conversations',
    '0 2 * * *',  -- Daily at 2 AM
    $$
    DELETE FROM conversations 
    WHERE created_at < NOW() - INTERVAL '90 days';
    $$
);
```

---

### **SOC2 Compliance**

**Key Controls:**

| Control | Implementation |
|---------|---------------|
| **Access Control** | RLS + RBAC + JWT |
| **Audit Logging** | Every DB write logged |
| **Data Encryption** | TLS 1.3 + TDE |
| **Change Management** | Git version control + CI/CD |
| **Incident Response** | Alerting (Prometheus) + on-call rotation |

**Audit Table:**

```sql
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    
    action TEXT NOT NULL,  -- "CREATE", "UPDATE", "DELETE"
    table_name TEXT NOT NULL,
    record_id UUID,
    
    old_values JSONB,
    new_values JSONB,
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_log(tenant_id, created_at);
```

**Audit Trigger:**

```sql
CREATE OR REPLACE FUNCTION audit_trigger_func() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (tenant_id, action, table_name, record_id, old_values, new_values)
    VALUES (
        NEW.tenant_id,
        TG_OP,
        TG_TABLE_NAME,
        NEW.goal_id,  -- Adjust per table
        row_to_json(OLD),
        row_to_json(NEW)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_goals_trigger
AFTER INSERT OR UPDATE OR DELETE ON goals
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

---

## 🛡️ 7. Security Audit

### **Security Checklist**

**Before Production Deployment:**

- [ ] RLS enabled on all tenant-scoped tables
- [ ] JWT secret rotated and stored in secrets manager
- [ ] TLS 1.3 enforced (no HTTP)
- [ ] CORS configured (whitelist frontend domains)
- [ ] Rate limiting enabled (100 requests/minute per user)
- [ ] SQL injection tests passed (use parameterized queries only)
- [ ] Dependency scan (no critical CVEs)
- [ ] Secrets not in code (use environment variables)
- [ ] Audit logging enabled
- [ ] GDPR endpoints tested (export, delete)
- [ ] Backup restoration tested
- [ ] Incident response plan documented

---

### **Penetration Testing**

**Recommended Tools:**

1. **OWASP ZAP** (automated web app scanner)
2. **Burp Suite** (manual testing)
3. **SQLMap** (SQL injection testing)
4. **Nmap** (network scanning)

**Annual third-party audit for SOC2 Type II compliance.**

---

## 🎯 Next Steps

1. **Review [Data Architecture](./Data-Architecture.md)** for RLS schema design
2. **Review [Observability Architecture](./Observability Architecture.md)** for audit logging
3. **Start Week 1** of [Implementation Roadmap](./Implementation-Roadmap.md)

**Security is not optional! 🔐**

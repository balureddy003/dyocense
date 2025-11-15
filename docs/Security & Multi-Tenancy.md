Security & Multi-Tenancy
Tenant Isolation
Database Level:

Row-Level Security (RLS): Every table has tenant_id policy
Connection Pooling: Set app.current_tenant_id session variable per request
Application Level:

JWT Token: Contains tenant_id claim
API Gateway: Validates tenant_id matches authenticated user
Data Encryption:

At Rest: PostgreSQL Transparent Data Encryption (TDE) or disk encryption
In Transit: TLS 1.3 for all connections
Secrets: HashiCorp Vault or AWS Secrets Manager
Authentication & Authorization
Stack: OAuth2 + JWT tokens

Roles:

Admin: Full access to tenant data
Manager: View all, edit goals/tasks
User: View own goals, limited editing
RBAC: PostgreSQL roles + application-level checks


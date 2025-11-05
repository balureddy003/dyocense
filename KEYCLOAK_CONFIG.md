# Keycloak Configuration Guide

## Quick Start (Development)

### 1. Update `.env` file

Add Keycloak credentials. Choose ONE of the two authentication methods:

#### Option A: Service Account (Recommended for production)
```properties
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_CLIENT_ID=admin-cli
KEYCLOAK_CLIENT_SECRET=your-client-secret
```

#### Option B: Username/Password (For development)
```properties
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_CLIENT_ID=admin-cli
KEYCLOAK_USERNAME=admin
KEYCLOAK_PASSWORD=admin
```

### 2. Start Keycloak

```bash
docker compose up -d keycloak
```

### 3. Verify Keycloak is Running

```bash
curl http://localhost:8080/auth/realms/master
```

Should return realm information (not 404).

### 4. Restart Backend Services

```bash
# Kill existing services
pkill -f uvicorn

# Restart with Keycloak support
python -m uvicorn services.accounts.main:app --reload --port 8000
```

You should see:
```
✅ Connected to Keycloak at http://localhost:8080
```

## Keycloak Setup for Development

### Create Service Account

1. Open Keycloak Admin Console: `http://localhost:8080/auth/admin`
2. Default credentials: `admin` / `admin`
3. Navigate to: **Clients** → **admin-cli**
4. Go to **Service Account Roles**
5. Click **Assign Roles**
6. Add: **realm-admin**
7. Go to **Credentials** tab
8. Copy the **Client Secret**
9. Add to `.env`:
   ```properties
   KEYCLOAK_CLIENT_SECRET=<your-secret>
   KEYCLOAK_USERNAME=  # Leave empty when using client_secret
   KEYCLOAK_PASSWORD=  # Leave empty when using client_secret
   ```

## Fallback Behavior

If Keycloak is not configured or unreachable:

✅ **System continues to work**
- Tenants are created in MongoDB only
- No Keycloak realms provisioned
- User gets demo token instead of proper credentials
- Warning logged: `"Keycloak credentials not configured. Proceeding with database-only tenant creation."`

Users can still:
- Access the platform with demo tokens
- Use the API
- Create projects and runs

But they:
- ❌ Cannot login through Keycloak
- ❌ Cannot manage realms
- ❌ Cannot enforce SSO

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `KEYCLOAK_SERVER_URL` | `http://localhost:8080` | Keycloak server endpoint |
| `KEYCLOAK_CLIENT_ID` | `admin-cli` | OAuth2 client ID |
| `KEYCLOAK_CLIENT_SECRET` | (none) | Client secret for service account auth |
| `KEYCLOAK_USERNAME` | (none) | Username for password-based auth |
| `KEYCLOAK_PASSWORD` | (none) | Password for password-based auth |

## Verification

### Check if Keycloak is Initialized

Look for this log message on startup:
```
✅ Connected to Keycloak at http://localhost:8080
```

Or this if not configured:
```
⚠️  Keycloak credentials not configured. Proceeding with database-only tenant creation.
```

### Test Tenant Creation with Keycloak

1. Go to `http://localhost:5173/buy`
2. Select a plan and complete signup
3. Check Keycloak Admin Console:
   - Navigate to **Realms**
   - You should see a new realm with the tenant name
4. In the realm, check **Users** for the owner account

## Troubleshooting

### "client_secret or (username, password) must be provided"

This is a warning, not an error. It means:
- Keycloak is NOT being used for this session
- System will fall back to demo tokens
- This is normal in development when credentials aren't configured

**Solution:** Add credentials to `.env` file as shown above.

### "Failed to connect to Keycloak"

Possible causes:
1. Keycloak not running
2. Wrong server URL
3. Invalid credentials

**Solutions:**
```bash
# Check if Keycloak is running
docker ps | grep keycloak

# Verify server URL is correct
curl http://localhost:8080/auth

# Check credentials in admin console
http://localhost:8080/auth/admin
```

### Tenants Created But No Keycloak Realm

This happens when Keycloak credentials aren't configured. Check logs for:
```
Keycloak credentials not configured
```

To fix:
1. Configure credentials in `.env`
2. Restart services
3. Create new tenant

## Production Checklist

- [ ] Use service account authentication (not username/password)
- [ ] Store `KEYCLOAK_CLIENT_SECRET` in secure vault
- [ ] Use HTTPS for Keycloak server URL
- [ ] Configure realm-level policies (passwords, MFA, etc.)
- [ ] Enable audit logging in Keycloak
- [ ] Set up backup for Keycloak database
- [ ] Test failover behavior (what happens if Keycloak is down?)
- [ ] Monitor Keycloak performance and logs

## Related Documentation

- [Keycloak Admin REST API](https://www.keycloak.org/docs/latest/server_admin/index.html#admin-rest-api)
- [python-keycloak Documentation](https://python-keycloak.readthedocs.io/)
- [Dyocense Phase 1 Implementation](./PHASE1_IMPLEMENTATION.md)

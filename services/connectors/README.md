# Connectors Service

The Connectors service manages data source integrations with secure credential storage, OAuth flows, and connection testing.

## Features

- **Secure Credential Storage**: All API keys and tokens are encrypted using Fernet (symmetric encryption)
- **Connector Testing**: Validate credentials before saving
- **OAuth Support**: Ready for OAuth2 flows (Google Drive, Xero, Shopify, etc.)
- **Multi-Tenant**: Isolated connector configurations per tenant
- **Health Monitoring**: Track connector status and sync information

## Supported Connectors

### Finance
- **Xero** (OAuth2) - UK accounting platform
- **Sage** (API Key) - UK accounting
- **QuickBooks** (OAuth2) - US accounting
- **Stripe** (API Key) - Payment processing

### E-commerce & POS
- **Shopify** (OAuth2) - E-commerce platform
- **WooCommerce** (API Key) - WordPress e-commerce
- **Square** (OAuth2) - POS system

### Storage & CRM
- **Google Drive** (OAuth2) - Cloud storage
- **HubSpot** (OAuth2) - CRM
- **Custom REST API** (Custom) - Any REST API
- **PostgreSQL** (Basic Auth) - Database

## API Endpoints

### Connector Management

```bash
# Get connector catalog
GET /v1/catalog

# Create a connector
POST /v1/connectors
{
  "connector_type": "xero",
  "display_name": "Main Xero Account",
  "config": {
    "access_token": "..."
  },
  "sync_frequency": "daily"
}

# List tenant's connectors
GET /v1/connectors
GET /v1/connectors?status=active

# Get specific connector
GET /v1/connectors/{connector_id}

# Update connector
PUT /v1/connectors/{connector_id}

# Delete connector
DELETE /v1/connectors/{connector_id}
```

### Testing

```bash
# Test existing connector
POST /v1/connectors/{connector_id}/test

# Test configuration before saving
POST /v1/connectors/test
{
  "connector_type": "stripe",
  "config": {
    "api_key": "sk_test_..."
  }
}
```

## Security

### Encryption

All connector credentials are encrypted using Fernet (symmetric encryption) before storage:

1. **Encryption Key**: Set `CONNECTOR_ENCRYPTION_KEY` environment variable
2. **Key Generation**: Run `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
3. **Storage**: Encrypted credentials stored in MongoDB
4. **Decryption**: Only happens server-side, never exposed in API responses

### Environment Variables

```bash
# Required for production
CONNECTOR_ENCRYPTION_KEY=<base64-encoded-fernet-key>

# MongoDB connection
MONGO_URI=mongodb://localhost:27017

# CORS (frontend origin)
CORS_ORIGINS=http://localhost:5173
```

### Best Practices

1. **Never log decrypted credentials**
2. **Rotate encryption keys** periodically
3. **Use OAuth2** for connectors that support it
4. **Test connections** before marking active
5. **Monitor connector health** regularly

## Development

### Run Locally

```bash
# Install dependencies
pip install fastapi uvicorn pymongo cryptography httpx pydantic

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set environment variable
export CONNECTOR_ENCRYPTION_KEY=<your-key>
export MONGO_URI=mongodb://localhost:27017

# Run service
python -m uvicorn services.connectors.main:app --reload --port 8009
```

### Testing

```bash
# Health check
curl http://localhost:8009/health

# Get catalog
curl http://localhost:8009/v1/catalog

# Create test connector (with auth)
curl -X POST http://localhost:8009/v1/connectors \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "connector_type": "stripe",
    "display_name": "Test Stripe",
    "config": {
      "api_key": "sk_test_..."
    }
  }'
```

## OAuth Flow (Coming Soon)

For OAuth2 connectors, the flow will be:

1. **Initiate**: Frontend redirects to `/v1/oauth/{connector_type}/authorize`
2. **Callback**: Provider redirects back to `/v1/oauth/{connector_type}/callback`
3. **Exchange**: Backend exchanges code for tokens
4. **Store**: Tokens encrypted and stored
5. **Refresh**: Auto-refresh expired tokens

## Connector Testing

Each connector type has a dedicated test method:

- **API Key**: Validates key works
- **OAuth**: Checks token validity
- **Database**: Tests connection
- **REST API**: Makes test request

Test results include:
- Success/failure status
- Error messages
- Connection details (without exposing credentials)

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (React App)    │
└────────┬────────┘
         │ HTTPS + Bearer Token
         ↓
┌─────────────────┐
│ Connectors API  │
│   (FastAPI)     │
├─────────────────┤
│ - Auth Check    │
│ - Encryption    │
│ - Testing       │
│ - CRUD          │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│    MongoDB      │
│ (Encrypted)     │
└─────────────────┘
```

## Future Enhancements

- [ ] OAuth2 authorization flows
- [ ] Automatic token refresh
- [ ] Webhook support for real-time sync
- [ ] Data preview endpoints
- [ ] Connector health monitoring
- [ ] Usage analytics
- [ ] Rate limiting per connector
- [ ] Batch operations
- [ ] Connector templates/presets

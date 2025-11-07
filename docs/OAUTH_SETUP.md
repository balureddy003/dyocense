# OAuth Social Login Setup Guide for SMBs

Dyocense supports social login with the most popular business authentication providers used by SMBs:

- **Google** (Gmail, Google Workspace) - Most widely used
- **Microsoft** (Outlook, Microsoft 365) - Common in businesses
- **Apple** (Apple ID) - iPhone users, privacy-focused

## Quick Start

1. Choose which providers you want to enable (we recommend starting with Google)
2. Register your app with the provider(s)
3. Add credentials to `.env` file
4. Restart your backend server
5. Users can now sign in with social accounts!

---

## Google OAuth Setup (Recommended First)

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project (or select existing)
3. Enable "Google+ API" or "Google Identity"
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Choose **Web application**
6. Add authorized redirect URIs:
   - Development: `http://localhost:5173/auth/callback/google`
   - Production: `https://yourdomain.com/auth/callback/google`
7. Copy the **Client ID** and **Client Secret**

### 2. Add to `.env` file

```bash
OAUTH_GOOGLE_CLIENT_ID=123456789-abc123.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz789
```

### 3. Restart Backend

```bash
python -m uvicorn services.kernel.main:app --reload --port 8001
```

---

## Microsoft OAuth Setup

### 1. Register App in Azure

1. Go to [Azure Portal - App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
2. Click **New registration**
3. Name: "Dyocense App"
4. Supported account types: **Accounts in any organizational directory and personal Microsoft accounts**
5. Redirect URI:
   - Platform: **Web**
   - URI: `http://localhost:5173/auth/callback/microsoft` (dev) or your production URL
6. Click **Register**

### 2. Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add description: "Dyocense OAuth"
4. Choose expiration (recommend 24 months for SMB simplicity)
5. Copy the **Value** (this is your client secret - save it now, can't view again!)

### 3. Copy Application ID

1. Go to **Overview**
2. Copy **Application (client) ID**

### 4. Add to `.env` file

```bash
OAUTH_MICROSOFT_CLIENT_ID=12345678-1234-1234-1234-123456789abc
OAUTH_MICROSOFT_CLIENT_SECRET=abc123~xyz789-ABC.DEF_GHI
```

---

## Apple OAuth Setup (Optional - Requires Apple Developer Account)

### 1. Create Service ID

1. Go to [Apple Developer](https://developer.apple.com/account/resources/identifiers/list/serviceId)
2. Click **+** to create new identifier
3. Select **Services IDs**, click Continue
4. Register a service ID (e.g., `com.yourcompany.dyocense`)
5. Enable **Sign in with Apple**
6. Configure domains and redirect URLs:
   - Domain: `yourdomain.com` (or `localhost` for dev)
   - Return URL: `https://yourdomain.com/auth/callback/apple`

### 2. Create Key for Sign in with Apple

1. Go to **Keys** in Apple Developer
2. Click **+** to create new key
3. Enable **Sign in with Apple**
4. Download the key file (`.p8`)
5. Note the **Key ID** and **Team ID**

### 3. Generate Client Secret

Apple requires generating a JWT as client secret. Use this Python script:

```python
import jwt
import time

key_id = "YOUR_KEY_ID"
team_id = "YOUR_TEAM_ID"
client_id = "com.yourcompany.dyocense"  # Your Service ID
key_file = "AuthKey_XXXXXXXXXX.p8"  # Your downloaded key

with open(key_file, 'r') as f:
    private_key = f.read()

headers = {"kid": key_id, "alg": "ES256"}
payload = {
    "iss": team_id,
    "iat": int(time.time()),
    "exp": int(time.time()) + 86400 * 180,  # 6 months
    "aud": "https://appleid.apple.com",
    "sub": client_id
}

client_secret = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
print(client_secret)
```

### 4. Add to `.env` file

```bash
OAUTH_APPLE_CLIENT_ID=com.yourcompany.dyocense
OAUTH_APPLE_CLIENT_SECRET=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Testing Your Setup

### 1. Check Enabled Providers

```bash
curl http://localhost:8001/api/accounts/v1/auth/providers
```

Should return:
```json
{
  "enabled_providers": ["google", "microsoft"],
  "providers": {
    "google": {
      "name": "Google",
      "description": "Sign in with Gmail or Google Workspace",
      ...
    }
  }
}
```

### 2. Test Login Flow

1. Go to your login page: `http://localhost:5173/login`
2. Click "Continue with Google" (or other provider)
3. Complete authentication with the provider
4. You should be redirected back and logged in!

---

## Common Issues

### "OAuth provider not configured"

- Check that your `.env` file has the correct environment variables
- Both `CLIENT_ID` and `CLIENT_SECRET` must be set
- Restart your backend server after adding credentials

### "Redirect URI mismatch"

- Make sure the redirect URI in your provider settings EXACTLY matches:
  - Format: `http://localhost:5173/auth/callback/{provider}`
  - Provider must be: `google`, `microsoft`, or `apple` (lowercase)
- No trailing slashes

### "Invalid client secret" (Apple)

- Apple client secrets expire (usually 6 months)
- Regenerate using the JWT script above
- Update your `.env` file

### Users can't find their account

- OAuth creates a NEW user if email doesn't exist in any tenant
- For existing users: They should log in with their OAuth email at least once
- The system will link their OAuth account to existing email

---

## Production Checklist

- [ ] Update redirect URIs to use HTTPS production URLs
- [ ] Set `APP_BASE_URL` environment variable to production domain
- [ ] Regenerate any test credentials with production-appropriate expiration
- [ ] Test login flow with real user accounts
- [ ] Enable HTTPS/SSL for your domain
- [ ] Consider which providers your target SMBs use most (usually Google + Microsoft)

---

## SMB Best Practices

### Which Providers Should You Enable?

**Minimum (covers 80% of SMBs):**
- ✅ Google (Gmail, Google Workspace)

**Recommended (covers 95% of SMBs):**
- ✅ Google
- ✅ Microsoft (Outlook, Office 365)

**Complete (covers 99% of SMBs):**
- ✅ Google
- ✅ Microsoft
- ✅ Apple

### Cost

- **Google**: Free (included in Google Cloud free tier)
- **Microsoft**: Free (Azure app registration is free)
- **Apple**: Requires Apple Developer account ($99/year)

### User Experience

Most SMB owners and employees use:
1. **Google** for personal Gmail or Google Workspace for business
2. **Microsoft** for Outlook.com or Microsoft 365
3. **Apple** for iPhone users who prefer Apple ID

Enabling just Google captures most users with minimal setup effort!

---

## Security Notes

- Store client secrets securely (use environment variables, never commit to git)
- Use HTTPS in production (OAuth requires secure redirect URIs)
- Consider secret rotation every 6-12 months
- Monitor OAuth provider status pages for outages
- Keep backend dependencies updated (especially `httpx` and OAuth libraries)

---

## Support

For OAuth setup issues:
1. Check provider documentation (links above)
2. Verify redirect URIs match exactly
3. Test with curl commands to isolate frontend vs backend issues
4. Check backend logs for detailed error messages

# Quick Start: Google OAuth Setup

This is the fastest way to enable social login for your SMB deployment. Google is the most commonly used provider and takes only 5 minutes to set up.

## Step 1: Get Google OAuth Credentials

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new project (or select existing one)
3. Click **"Create Credentials"** → **"OAuth 2.0 Client ID"**
4. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: "Dyocense"
   - User support email: your email
   - Developer contact: your email
   - Click **"Save and Continue"** through remaining screens
5. Application type: **Web application**
6. Name: "Dyocense SMB App"
7. Authorized redirect URIs:
   - Click **"+ Add URI"**
   - Enter: `http://localhost:5173/auth/callback/google`
   - For production, add: `https://yourdomain.com/auth/callback/google`
8. Click **"Create"**
9. Copy your **Client ID** and **Client Secret**

## Step 2: Configure Your Backend

Add these lines to your `.env` file (or create one from `.env.smb`):

```bash
# Google OAuth
OAUTH_GOOGLE_CLIENT_ID=123456789-abcdefghijk.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz789
```

## Step 3: Restart Backend

```bash
python -m uvicorn services.kernel_unified.main:app --reload --port 8001
```

## Step 4: Test It!

1. Open your UI: http://localhost:5173/login
2. You should see a **"Continue with Google"** button
3. Click it and sign in with any Google account
4. You'll be automatically redirected back and logged in!

## What Happens Behind the Scenes

1. **First time user**: Creates a new tenant and user account automatically
2. **Existing email**: Links Google account to existing email
3. **Multi-tenant**: If email exists in multiple tenants, user can choose

## Troubleshooting

### "OAuth provider not configured"

Your backend can't see the environment variables. Check:

```bash
# Test if backend sees your config
curl http://localhost:8001/api/accounts/v1/auth/providers

# Should return:
# {"enabled_providers": ["google"], ...}
```

If `enabled_providers` is empty:
- Make sure `.env` file has the OAuth variables
- Restart the backend server
- Check that variable names match exactly: `OAUTH_GOOGLE_CLIENT_ID` (not `GOOGLE_CLIENT_ID`)

### "Redirect URI mismatch"

The URL you configured in Google Console must EXACTLY match what your app uses:

- ✅ Correct: `http://localhost:5173/auth/callback/google`
- ❌ Wrong: `http://localhost:5173/auth/callback/google/`  (trailing slash)
- ❌ Wrong: `http://127.0.0.1:5173/auth/callback/google`  (use localhost, not 127.0.0.1)

### Button doesn't appear

1. Check browser console for errors
2. Make sure UI can reach backend: http://localhost:8001/health
3. Clear browser cache and reload

## Production Deployment

When deploying to production:

1. Add production redirect URI in Google Console:
   ```
   https://yourdomain.com/auth/callback/google
   ```

2. Update `.env` (if you hardcoded redirect URI):
   ```bash
   APP_BASE_URL=https://yourdomain.com
   ```

3. Restart backend

That's it! Your production users can now sign in with Google.

## Add More Providers (Optional)

Once Google works, you can add Microsoft and Apple following the same pattern. See `docs/OAUTH_SETUP.md` for detailed instructions.

**Recommendation for SMBs**: Start with just Google. It covers 80% of small business users and requires minimal setup. Add Microsoft later if needed.

## Next Steps

- ✅ Test Google login with personal Gmail
- ✅ Test with Google Workspace account (if you have one)
- ✅ Invite team members to try it
- ⏸️ Consider adding Microsoft OAuth (optional)
- ⏸️ Consider adding Apple OAuth (optional, requires $99/year Apple Developer account)

## Benefits You'll See

- **Faster signups**: Users create accounts in 2 clicks
- **Fewer support tickets**: No password reset emails
- **Higher conversion**: Less friction = more signups
- **Better security**: Google handles authentication
- **Mobile-friendly**: Works great on phones

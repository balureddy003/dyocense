# Login Flow & Profile Setup Fix

## Problem

Users were getting stuck in a loop after login:

1. User completes registration → Auto-logged in
2. Login page checks: "No profile? → Redirect to /profile"
3. Profile setup page shows "Tell us about your business" form
4. **This happened EVERY time they logged in**, creating a frustrating loop

## Root Cause

The `LoginPage` was forcing all authenticated users without a profile to complete the profile setup before accessing the application. This made the profile setup **mandatory** instead of **optional**.

## Solution Implemented

### 1. Made Profile Setup Optional (`LoginPage.tsx`)

**Before:**

```typescript
if (authenticated && !profile) {
  navigate("/profile", { replace: true });  // Force profile setup
  return;
}

if (authenticated && profile) {
  resolveRedirect(navigate, redirectTarget);  // Only redirect if has profile
}
```

**After:**

```typescript
if (authenticated) {
  resolveRedirect(navigate, redirectTarget);  // Redirect regardless of profile
}
```

**Impact:** Users can now access the app immediately after login, whether they have a profile or not.

### 2. Added "Skip for now" Button (`ProfileSetupPage.tsx`)

**Changes:**

- Added a skip button next to the "Continue to Dashboard" button
- Removed auto-redirect logic when user has a profile (let them edit if they want)
- Users can now choose to fill out profile later

**Code:**

```typescript
<button
  type="submit"
  className="w-full sm:w-auto px-8 py-4 rounded-full bg-gradient-to-r from-primary to-blue-600 text-white font-semibold..."
>
  Continue to Dashboard
</button>
<button
  type="button"
  onClick={() => navigate("/home")}
  className="w-full sm:w-auto px-8 py-4 rounded-full border-2 border-gray-300 text-gray-700 font-semibold..."
>
  Skip for now
</button>
```

**Impact:** Users who don't want to fill out their business description can skip and go straight to the dashboard.

### 3. Streamlined Registration Flow (`PurchasePage.tsx`)

**Changes:**

- After successful registration, user is auto-logged in
- Instead of showing success page with buttons, redirect directly to `/home`
- User gets immediate access to the application

**Before:**

```typescript
setOnboarding(details);
setStep("success");  // Show success page with "Go to Login" button
```

**After:**

```typescript
setOnboarding(details);

// Auto-login the user
await loginWithToken({
  apiToken: registrationResponse.api_token,
  tenantId: registrationResponse.tenant_id,
  email: formData.email,
  remember: true,
});

// Redirect directly to home
navigate("/home", { replace: true });
```

**Impact:** New users go straight from registration to the dashboard without manual login steps.

## User Flows

### Registration Flow (New Users)

**Before:**

1. Fill registration form
2. See success page
3. Click "Go to Login"
4. Enter credentials again
5. Redirected to profile setup (mandatory)
6. Fill out business description
7. Finally reach dashboard

**After:**

1. Fill registration form
2. **Automatically logged in and redirected to dashboard** 🎉

### Login Flow (Returning Users)

**Before:**

1. Enter credentials
2. Forced to profile setup page (if no profile saved)
3. Stuck in loop - must fill out form to continue
4. Finally reach dashboard

**After:**

1. Enter credentials
2. **Immediately redirected to dashboard** 🎉
3. Can optionally fill out profile from settings

### Profile Setup Access

Users can still access profile setup:

- From settings/profile menu
- By navigating to `/profile` directly
- When they want to update business information
- But it's **never forced** on them

## Benefits

✅ **No More Loops**: Users never get stuck in profile setup
✅ **Faster Onboarding**: Registration → Dashboard in one step
✅ **Better UX**: Optional profile instead of mandatory blocker
✅ **User Choice**: Skip profile setup or fill it later
✅ **Immediate Value**: Access dashboard right away

## Testing

To test the fixes:

1. **New User Registration:**

   ```
   1. Go to /purchase?plan=free
   2. Fill out form and click "Start Free Trial"
   3. Should be redirected to /home immediately (no profile page)
   ```

2. **Returning User Login:**

   ```
   1. Go to /login
   2. Enter credentials
   3. Should go to /home (not forced to /profile)
   ```

3. **Optional Profile Setup:**

   ```
   1. Navigate to /profile manually
   2. See form with "Skip for now" button
   3. Click skip → redirects to /home
   4. Or fill out form → saves profile and redirects to /home
   ```

## Files Modified

1. **`apps/ui/src/pages/LoginPage.tsx`**
   - Removed mandatory profile check
   - Simplified redirect logic

2. **`apps/ui/src/pages/ProfileSetupPage.tsx`**
   - Added "Skip for now" button
   - Removed auto-redirect for users with profiles

3. **`apps/ui/src/pages/PurchasePage.tsx`**
   - Implemented auto-login after registration
   - Direct redirect to `/home` instead of showing success page

## Future Enhancements

Consider these optional improvements:

1. **Profile Completion Nudge**: Show a dismissible banner in dashboard suggesting profile completion
2. **Progressive Disclosure**: Ask for profile info gradually (e.g., during first playbook creation)
3. **Profile Benefits**: Highlight what users get by completing profile (better AI suggestions, etc.)
4. **Quick Profile**: Single-field profile option (just business type) with full form as optional
5. **Welcome Tour**: Interactive product tour instead of profile form

## Rollback Instructions

If these changes cause issues, revert by:

```bash
cd apps/ui
git checkout HEAD~1 -- src/pages/LoginPage.tsx
git checkout HEAD~1 -- src/pages/ProfileSetupPage.tsx
git checkout HEAD~1 -- src/pages/PurchasePage.tsx
```

Or manually restore:

- LoginPage: Add back profile check before redirect
- ProfileSetupPage: Remove skip button
- PurchasePage: Show success page instead of auto-redirect

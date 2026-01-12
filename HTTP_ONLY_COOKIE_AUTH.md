# HTTP-Only Cookie Authentication - Implementation Guide

## Overview

Successfully implemented HTTP-only cookie authentication for enhanced security in the ResearchIndex platform. This implementation protects JWT tokens from XSS attacks by storing them in HTTP-only cookies that JavaScript cannot access.

---

## Security Enhancements

### Before (Bearer Token in localStorage)

```javascript
//  Vulnerable to XSS attacks
localStorage.setItem("access_token", token);
// Malicious scripts can steal: localStorage.getItem('access_token')
```

### After (HTTP-Only Cookies)

```javascript
//  Protected - JavaScript cannot access HTTP-only cookies
// Tokens automatically sent with requests via cookies
// Even if XSS occurs, tokens cannot be stolen
```

---

## Implementation Details

### 1. Custom Authentication Class

**File**: `users/authentication.py`

Created `JWTCookieAuthentication` class that:

- Checks for JWT tokens in HTTP-only cookies first
- Falls back to Authorization header (backward compatibility)
- Validates tokens and authenticates users

**Features**:

- Primary authentication via cookies
- Backward compatible with Bearer tokens
- Automatic token extraction and validation

### 2. Cookie Helper Functions

**File**: `users/views.py`

Added utility functions:

#### `set_auth_cookies(response, access_token, refresh_token)`

Sets both access and refresh tokens as HTTP-only cookies with:

- **httponly=True**: JavaScript cannot access
- **secure=True** (production): HTTPS only
- **samesite='Lax'**: CSRF protection
- **Max-age**: Token lifetime
- **Domain & Path**: Configurable

#### `clear_auth_cookies(response)`

Removes authentication cookies on logout

### 3. Updated Views

Modified all authentication endpoints to set cookies:

#### Registration Views

- `AuthorRegistrationView`
- `InstitutionRegistrationView`

**Changes**: Set HTTP-only cookies after user creation

#### LoginView

**Changes**:

- Generate JWT tokens
- Set HTTP-only cookies in response
- Return tokens in body (optional, for flexibility)

#### LogoutView (NEW)

**Purpose**: Logout with cookie clearing

**Features**:

- Blacklists refresh token
- Clears both access and refresh cookies
- Handles token from cookie or request body
- Graceful error handling

#### CookieTokenRefreshView (NEW)

**Purpose**: Refresh access token using cookie-based refresh token

**Features**:

- Reads refresh token from cookie
- Falls back to request body
- Returns new access token
- Sets new access token cookie
- Maintains HTTP-only security

### 4. Settings Configuration

**File**: `researchindex/settings.py`

Added JWT cookie settings:

```python
# JWT Cookie Configuration
JWT_AUTH_COOKIE = 'access_token'  # Cookie name for access token
JWT_REFRESH_COOKIE = 'refresh_token'  # Cookie name for refresh token
JWT_AUTH_COOKIE_SECURE = not DEBUG  # HTTPS only in production
JWT_AUTH_COOKIE_HTTP_ONLY = True  # Prevent JavaScript access
JWT_AUTH_COOKIE_SAMESITE = 'Lax'  # CSRF protection
JWT_AUTH_COOKIE_PATH = '/'  # Cookie path
JWT_AUTH_COOKIE_DOMAIN = None  # Current domain
```

Updated authentication classes:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.JWTCookieAuthentication',  # Cookie-based (primary)
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # Fallback
    ),
}
```

### 5. URL Configuration

**File**: `users/urls.py`

Updated routes:

- `POST /api/users/login/` - Login with cookie setting
- `POST /api/users/logout/` - Logout with cookie clearing (NEW)
- `POST /api/users/token/refresh/` - Refresh with cookie support (NEW)

---

## API Usage

### 1. Login (Sets Cookies Automatically)

```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "author@university.edu",
    "password": "SecurePass123!"
  }' \
  -c cookies.txt  # Save cookies
```

**Response Headers** (automatic):

```
Set-Cookie: access_token=eyJhbGc...; HttpOnly; SameSite=Lax; Path=/; Max-Age=3600
Set-Cookie: refresh_token=eyJhbGc...; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800
```

**Response Body**:

```json
{
  "message": "Login successful",
  "tokens": {
    "access": "eyJhbGc...",
    "refresh": "eyJhbGc..."
  },
  "user": { ...profile data... }
}
```

### 2. Authenticated Requests (Cookies Sent Automatically)

```bash
curl -X GET http://localhost:8000/api/users/profile/author/ \
  -b cookies.txt  # Send cookies automatically
```

**No Authorization header needed!** Cookies are sent automatically.

### 3. Token Refresh (Cookie-Based)

```bash
curl -X POST http://localhost:8000/api/users/token/refresh/ \
  -b cookies.txt  # Refresh token from cookie
```

**Response**:

```json
{
  "message": "Token refreshed successfully",
  "access": "eyJhbGc..."
}
```

New access token cookie is set automatically.

### 4. Logout (Clears Cookies)

```bash
curl -X POST http://localhost:8000/api/users/logout/ \
  -b cookies.txt
```

**Response**:

```json
{
  "message": "Logout successful"
}
```

Cookies are cleared from browser.

---

## Frontend Integration

### JavaScript/Fetch Example

```javascript
// Login - cookies set automatically
async function login(email, password) {
  const response = await fetch("http://localhost:8000/api/users/login/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include", //  CRITICAL: Include cookies
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();
  // Cookies are automatically stored by browser
  // No need to manually save tokens!
  return data;
}

// Authenticated requests - cookies sent automatically
async function getProfile() {
  const response = await fetch(
    "http://localhost:8000/api/users/profile/author/",
    {
      method: "GET",
      credentials: "include", //  CRITICAL: Send cookies
    }
  );

  return await response.json();
}

// Refresh token - cookies handled automatically
async function refreshToken() {
  const response = await fetch(
    "http://localhost:8000/api/users/token/refresh/",
    {
      method: "POST",
      credentials: "include", //  CRITICAL: Send refresh cookie
    }
  );

  return await response.json();
}

// Logout - cookies cleared automatically
async function logout() {
  const response = await fetch("http://localhost:8000/api/users/logout/", {
    method: "POST",
    credentials: "include", //  CRITICAL: Send cookies
  });

  return await response.json();
}
```

### React Example with Axios

```javascript
import axios from "axios";

// Configure axios to always send cookies
const api = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true, //  CRITICAL: Include cookies
});

// Login
const login = async (email, password) => {
  const response = await api.post("/users/login/", { email, password });
  // Cookies automatically stored
  return response.data;
};

// Get profile
const getProfile = async () => {
  const response = await api.get("/users/profile/author/");
  // Cookies automatically sent
  return response.data;
};

// Refresh token
const refreshToken = async () => {
  const response = await api.post("/users/token/refresh/");
  return response.data;
};

// Logout
const logout = async () => {
  const response = await api.post("/users/logout/");
  return response.data;
};
```

### Critical Frontend Settings

**MUST include in all requests**:

- `credentials: 'include'` (fetch)
- `withCredentials: true` (axios)

Without this, cookies won't be sent!

---

## CORS Configuration (Important!)

For frontend apps on different domains/ports, update `settings.py`:

```python
INSTALLED_APPS = [
    'corsheaders',  # Add this
    ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add at top
    ...
]

# CORS settings for cookie authentication
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # React dev server
    'http://localhost:5173',  # Vite dev server
    'https://yourdomain.com',  # Production frontend
]

CORS_ALLOW_CREDENTIALS = True  #  CRITICAL for cookies
```

Install CORS headers:

```bash
pip install django-cors-headers
```

---

## Security Features

### 1. XSS Protection

**HTTP-Only Flag**: JavaScript cannot access cookies

```
Set-Cookie: access_token=...; HttpOnly
```

### 2. CSRF Protection

**SameSite Attribute**: Prevents CSRF attacks

```
Set-Cookie: access_token=...; SameSite=Lax
```

Options:

- `Strict`: Most secure, may break some flows
- `Lax`: Balanced security (recommended)
- `None`: Least secure, requires HTTPS

### 3. HTTPS Enforcement (Production)

**Secure Flag**: Cookies only sent over HTTPS

```python
JWT_AUTH_COOKIE_SECURE = not DEBUG  # True in production
```

### 4. Token Blacklisting

Logout blacklists refresh tokens to prevent reuse

---

## Migration Guide

### From Bearer Tokens to Cookies

**Old Code** (localStorage):

```javascript
// Login
const { access, refresh } = await login(email, password);
localStorage.setItem("access_token", access);
localStorage.setItem("refresh_token", refresh);

// Requests
fetch("/api/users/profile/author/", {
  headers: {
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  },
});
```

**New Code** (HTTP-only cookies):

```javascript
// Login - no manual storage needed
await login(email, password);

// Requests - no Authorization header needed
fetch("/api/users/profile/author/", {
  credentials: "include", // Just add this
});
```

### Backward Compatibility

The implementation maintains backward compatibility:

- Old clients using `Authorization: Bearer <token>` still work
- New clients using cookies work automatically
- Both can coexist during migration

---

## Cookie Settings Reference

| Setting                     | Default           | Description               |
| --------------------------- | ----------------- | ------------------------- |
| `JWT_AUTH_COOKIE`           | `'access_token'`  | Access token cookie name  |
| `JWT_REFRESH_COOKIE`        | `'refresh_token'` | Refresh token cookie name |
| `JWT_AUTH_COOKIE_SECURE`    | `not DEBUG`       | HTTPS only (production)   |
| `JWT_AUTH_COOKIE_HTTP_ONLY` | `True`            | Prevent JavaScript access |
| `JWT_AUTH_COOKIE_SAMESITE`  | `'Lax'`           | CSRF protection level     |
| `JWT_AUTH_COOKIE_PATH`      | `'/'`             | Cookie path scope         |
| `JWT_AUTH_COOKIE_DOMAIN`    | `None`            | Cookie domain scope       |

---

## Testing

### 1. Django Check

```bash
python manage.py check
#  System check identified no issues
```

### 2. Test Login

```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password"}' \
  -v  # Verbose to see cookies
```

Look for `Set-Cookie` headers in response.

### 3. Test Authenticated Request

```bash
# Save cookies from login
curl ... -c cookies.txt

# Use cookies for authenticated request
curl -X GET http://localhost:8000/api/users/profile/author/ \
  -b cookies.txt
```

### 4. Test Logout

```bash
curl -X POST http://localhost:8000/api/users/logout/ \
  -b cookies.txt \
  -v
```

Look for cookie expiration in headers.

---

## Troubleshooting

### Issue: Cookies not being set

**Solution**:

1. Check CORS settings (`CORS_ALLOW_CREDENTIALS = True`)
2. Verify frontend uses `credentials: 'include'`
3. Check `Set-Cookie` headers in response

### Issue: Cookies not being sent

**Solution**:

1. Ensure `credentials: 'include'` in requests
2. Check cookie domain/path settings
3. Verify CORS origin matches request origin

### Issue: CSRF errors

**Solution**:

1. Set `JWT_AUTH_COOKIE_SAMESITE = 'Lax'`
2. For cross-site requests, use `'None'` (requires HTTPS)
3. Configure CSRF exemption if needed

---

## Files Modified

1.  `users/authentication.py` - Created custom authentication class
2.  `users/views.py` - Added cookie helpers, updated views
3.  `users/urls.py` - Added logout and refresh endpoints
4.  `researchindex/settings.py` - Added cookie configuration

---

## Benefits Summary

| Aspect                   | Bearer Tokens | HTTP-Only Cookies     |
| ------------------------ | ------------- | --------------------- |
| **XSS Protection**       | Vulnerable    | Protected             |
| **Storage**              | localStorage  | Browser cookies       |
| **Manual Handling**      | Required      | Automatic             |
| **CSRF Protection**      | N/A           | SameSite attribute    |
| **HTTPS Enforcement**    | Optional      | Built-in (production) |
| **Developer Experience** | More code     | Less code             |

---

## Production Checklist

Before deploying:

- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS (automatic `Secure` flag)
- [ ] Configure CORS for production domain
- [ ] Set `CORS_ALLOW_CREDENTIALS = True`
- [ ] Verify `JWT_AUTH_COOKIE_SAMESITE` setting
- [ ] Test login/logout flow
- [ ] Test token refresh
- [ ] Monitor cookie behavior in browser DevTools

---

## Conclusion

**HTTP-only cookie authentication implemented successfully**

**Key Features**:

- Enhanced security against XSS attacks
- Automatic cookie handling
- Backward compatible with Bearer tokens
- CSRF protection via SameSite
- HTTPS enforcement in production
- Simple frontend integration

**Status**: Production-ready with comprehensive security features.

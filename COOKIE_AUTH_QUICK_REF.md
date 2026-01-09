# HTTP-Only Cookie Authentication - Quick Reference

## What Changed?

### Authentication Flow

**Before**: Manual token management in localStorage  
**After**: Automatic cookie-based authentication

### Security Improvements

✅ **XSS Protection**: Tokens stored in HTTP-only cookies (JavaScript cannot access)  
✅ **CSRF Protection**: SameSite cookie attribute  
✅ **HTTPS Enforcement**: Secure flag in production  
✅ **Automatic Management**: Browser handles cookies automatically

---

## New Endpoints

### Logout

```
POST /api/users/logout/
```

- Blacklists refresh token
- Clears authentication cookies
- Requires authentication

### Token Refresh (Updated)

```
POST /api/users/token/refresh/
```

- Reads refresh token from cookie (or body)
- Returns new access token
- Sets new access token cookie

---

## Frontend Usage

### Critical Setting

**ALL requests must include**:

```javascript
credentials: "include"; // fetch
withCredentials: true; // axios
```

### Login Example

```javascript
const response = await fetch("http://localhost:8000/api/users/login/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "include", // ← Required
  body: JSON.stringify({ email, password }),
});
// Cookies set automatically by browser
```

### Authenticated Request Example

```javascript
const response = await fetch(
  "http://localhost:8000/api/users/profile/author/",
  {
    credentials: "include", // ← Sends cookies automatically
  }
);
```

### Logout Example

```javascript
await fetch("http://localhost:8000/api/users/logout/", {
  method: "POST",
  credentials: "include",
});
// Cookies cleared automatically
```

---

## CORS Setup (Required for Different Domains)

**Backend** (`settings.py`):

```python
INSTALLED_APPS = ['corsheaders', ...]

MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware', ...]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://yourdomain.com',
]

CORS_ALLOW_CREDENTIALS = True  # ← Critical for cookies
```

**Install**:

```bash
pip install django-cors-headers
```

---

## Cookie Settings

| Setting                     | Value             | Purpose                   |
| --------------------------- | ----------------- | ------------------------- |
| `JWT_AUTH_COOKIE`           | `'access_token'`  | Access token cookie name  |
| `JWT_REFRESH_COOKIE`        | `'refresh_token'` | Refresh token cookie name |
| `JWT_AUTH_COOKIE_HTTP_ONLY` | `True`            | Prevent XSS               |
| `JWT_AUTH_COOKIE_SECURE`    | `not DEBUG`       | HTTPS only (production)   |
| `JWT_AUTH_COOKIE_SAMESITE`  | `'Lax'`           | CSRF protection           |

---

## Response Headers (Automatic)

After login:

```
Set-Cookie: access_token=eyJ...; HttpOnly; SameSite=Lax; Max-Age=3600
Set-Cookie: refresh_token=eyJ...; HttpOnly; SameSite=Lax; Max-Age=604800
```

---

## Backward Compatibility

✅ Old clients using `Authorization: Bearer <token>` still work  
✅ New clients using cookies work automatically  
✅ Both can coexist during migration

---

## Common Issues

### Cookies not being set?

- Check CORS: `CORS_ALLOW_CREDENTIALS = True`
- Frontend: Use `credentials: 'include'`
- Check response headers for `Set-Cookie`

### Cookies not being sent?

- Frontend: Use `credentials: 'include'`
- Check cookie domain/path settings
- Verify CORS origin matches

### CSRF errors?

- Set `JWT_AUTH_COOKIE_SAMESITE = 'Lax'`
- For cross-origin: Use `'None'` (requires HTTPS)

---

## Testing Commands

### Login

```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass"}' \
  -c cookies.txt
```

### Authenticated Request

```bash
curl http://localhost:8000/api/users/profile/author/ \
  -b cookies.txt
```

### Logout

```bash
curl -X POST http://localhost:8000/api/users/logout/ \
  -b cookies.txt
```

---

## Files Changed

1. `users/authentication.py` - Custom cookie authentication
2. `users/views.py` - Cookie helpers, logout, refresh
3. `users/urls.py` - New endpoints
4. `researchindex/settings.py` - Cookie configuration

---

## Status

✅ **Implementation Complete**  
✅ **Security Enhanced**  
✅ **Backward Compatible**  
✅ **Production Ready**

---

## Next Steps

1. Update frontend to use `credentials: 'include'`
2. Configure CORS for production domain
3. Test login/logout flow
4. Remove localStorage token management
5. Deploy with HTTPS

---

**Need more details?** See `HTTP_ONLY_COOKIE_AUTH.md` for comprehensive documentation.

# Research Index Authentication API Documentation

## Overview

This API provides JWT-based authentication for two types of users:

- **Authors**: Individual researchers with detailed profile information
- **Institutions**: Organizations with basic profile information

## Base URL

```
http://localhost:8000/api/auth/
```

## Endpoints

### 1. Author Registration

**POST** `/api/auth/register/author/`

Register a new author account.

**Request Body:**

```json
{
  "email": "author@example.com",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "title": "Dr.",
  "full_name": "John Doe",
  "institute": "MIT",
  "designation": "Professor"
}
```

**Title Options:**

- `Dr.`
- `Prof.`
- `Mr.`
- `Ms.`
- `Mrs.`

**Response (201 Created):**

```json
{
  "message": "Author registered successfully",
  "user": {
    "email": "author@example.com",
    "user_type": "author"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 2. Institution Registration

**POST** `/api/auth/register/institution/`

Register a new institution account.

**Request Body:**

```json
{
  "email": "admin@institution.edu",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "institution_name": "Harvard University"
}
```

**Response (201 Created):**

```json
{
  "message": "Institution registered successfully",
  "user": {
    "email": "admin@institution.edu",
    "user_type": "institution"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 3. Login

**POST** `/api/auth/login/`

Login for both authors and institutions.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK) - Author:**

```json
{
  "message": "Login successful",
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "user": {
    "email": "author@example.com",
    "user_type": "author",
    "title": "Dr.",
    "full_name": "John Doe",
    "institute": "MIT",
    "designation": "Professor"
  }
}
```

**Response (200 OK) - Institution:**

```json
{
  "message": "Login successful",
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "user": {
    "email": "admin@institution.edu",
    "user_type": "institution",
    "institution_name": "Harvard University"
  }
}
```

**Response (401 Unauthorized):**

```json
{
  "error": "Invalid email or password"
}
```

---

### 4. Token Refresh

**POST** `/api/auth/token/refresh/`

Get a new access token using a refresh token.

**Request Body:**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 5. Author Profile

**GET** `/api/auth/profile/author/`

Get the authenticated author's profile.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "email": "author@example.com",
  "user_type": "author",
  "title": "Dr.",
  "full_name": "John Doe",
  "institute": "MIT",
  "designation": "Professor"
}
```

**Response (404 Not Found):**

```json
{
  "error": "Author profile not found"
}
```

---

### 6. Institution Profile

**GET** `/api/auth/profile/institution/`

Get the authenticated institution's profile.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "email": "admin@institution.edu",
  "user_type": "institution",
  "institution_name": "Harvard University"
}
```

**Response (404 Not Found):**

```json
{
  "error": "Institution profile not found"
}
```

---

## Authentication

This API uses JWT (JSON Web Tokens) for authentication. After login or registration, you'll receive:

1. **Access Token**: Short-lived token (60 minutes) for API requests
2. **Refresh Token**: Long-lived token (7 days) to get new access tokens

### Using Access Tokens

Include the access token in the Authorization header for protected endpoints:

```
Authorization: Bearer <access_token>
```

### Token Lifecycle

1. Login/Register → Receive access & refresh tokens
2. Use access token for API requests
3. When access token expires → Use refresh token to get new access token
4. When refresh token expires → User must login again

---

## Error Responses

### Validation Errors (400 Bad Request)

```json
{
  "email": ["This field is required."],
  "password": ["This password is too short."]
}
```

### Authentication Error (401 Unauthorized)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Permission Error (403 Forbidden)

```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## Testing the API

### Using cURL

**Author Registration:**

```bash
curl -X POST http://localhost:8000/api/auth/register/author/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "author@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "title": "Dr.",
    "full_name": "John Doe",
    "institute": "MIT",
    "designation": "Professor"
  }'
```

**Login:**

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "author@example.com",
    "password": "SecurePass123!"
  }'
```

**Get Profile:**

```bash
curl -X GET http://localhost:8000/api/auth/profile/author/ \
  -H "Authorization: Bearer <access_token>"
```

### Using Python Requests

```python
import requests

# Register
response = requests.post('http://localhost:8000/api/auth/register/author/', json={
    "email": "author@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "title": "Dr.",
    "full_name": "John Doe",
    "institute": "MIT",
    "designation": "Professor"
})
tokens = response.json()['tokens']

# Get Profile
headers = {'Authorization': f'Bearer {tokens["access"]}'}
profile = requests.get('http://localhost:8000/api/auth/profile/author/', headers=headers)
print(profile.json())
```

---

## Database Models

### CustomUser

- email (unique)
- password (hashed)
- user_type (author/institution/admin)
- is_active
- is_staff
- created_at
- updated_at

### Author

- user (OneToOne → CustomUser)
- title
- full_name
- institute
- designation

### Institution

- user (OneToOne → CustomUser)
- institution_name

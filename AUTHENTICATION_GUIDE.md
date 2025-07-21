# Authentication System Guide

This guide explains how to use the improved authentication system with pre-approved users and webhook synchronization.

## Overview

The new authentication system includes:

- **Enhanced User Management**: Users with detailed profiles including email, full name, roles, and approval status
- **Pre-approved Users List**: A list of users who are authorized to access the system
- **Webhook Integration**: External platform can sync users via webhook endpoints
- **Admin Interface**: Web UI for managing users and approved users list
- **Role-based Access Control**: Admin, Instructor, and Student roles with appropriate permissions

## User Database Structure

Users are stored in `backend/users_db.json` with the following structure:

```json
{
  "username": {
    "id": "username",
    "username": "username",
    "email": "user@example.com",
    "full_name": "Full Name",
    "role": "student|instructor|admin",
    "hashed_password": "bcrypt_hash",
    "disabled": false,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "external_id": "external_platform_id",
    "approved": true,
    "last_login": "2024-01-01T00:00:00"
  }
}
```

## Pre-approved Users List

The approved users list is stored in `backend/approved_users.json`:

```json
[
  {
    "external_id": "ext_001",
    "username": "aluno1",
    "email": "aluno1@example.com",
    "full_name": "Aluno Um",
    "role": "student"
  }
]
```

## API Endpoints

### Authentication
- `POST /auth/token` - Login (returns JWT token)
- `GET /auth/me` - Get current user info
- `POST /auth/change-password` - Change password (authenticated user)
- `POST /auth/reset-password` - Reset password (admin only)

### User Management (Admin Only)
- `GET /auth/users` - List all users
- `POST /auth/users` - Create new user
- `PUT /auth/users/{username}` - Update user
- `DELETE /auth/users/{username}` - Delete user

### Approved Users Management (Admin Only)
- `GET /auth/approved-users` - Get approved users list
- `POST /auth/approved-users` - Add user to approved list
- `DELETE /auth/approved-users/{username}` - Remove from approved list

### Webhook (External Platform)
- `POST /auth/webhook/users` - Sync users from external platform

## Environment Variables

Add these to your `.env` file in the backend directory:

```env
SECRET_KEY=your-jwt-secret-key-here
WEBHOOK_SECRET=your-webhook-secret-key-here
OPENAI_API_KEY=your-openai-api-key
```

## Testing the System

### 1. Start the Backend

```bash
cd backend
uvicorn main_simple:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the Frontend

```bash
npm run dev
```

### 3. Login with Default Users

Default users are created automatically:
- **Username**: `admin`, **Password**: `adminpass`, **Role**: admin
- **Username**: `instrutor`, **Password**: `instrutorpass`, **Role**: instructor

### 4. Access User Management (Admin Only)

1. Login as admin
2. Navigate to "Gerenciar Usuários" in the sidebar
3. You can:
   - View all users and their status
   - Create new users
   - Update user roles and approval status
   - Manage the approved users list
   - Disable/enable users

### 5. Test Webhook Integration

Send a POST request to `http://localhost:8000/auth/webhook/users` with the following headers:

```
Content-Type: application/json
X-Hub-Signature-256: sha256=HMAC_SHA256_SIGNATURE
```

Example webhook payload:

```json
{
  "external_id": "ext_123",
  "username": "novousuario",
  "email": "novo@example.com",
  "full_name": "Novo Usuário",
  "role": "student",
  "action": "create"
}
```

### Generate Webhook Signature

Use this Python script to generate the correct signature:

```python
import hmac
import hashlib
import json

webhook_secret = "webhook-secret-key"  # Same as WEBHOOK_SECRET in .env
payload = {
    "external_id": "ext_123",
    "username": "novousuario",
    "email": "novo@example.com",
    "full_name": "Novo Usuário",
    "role": "student",
    "action": "create"
}

payload_bytes = json.dumps(payload).encode()
signature = hmac.new(
    webhook_secret.encode(),
    payload_bytes,
    hashlib.sha256
).hexdigest()

print(f"X-Hub-Signature-256: sha256={signature}")
```

### 6. Test with cURL

```bash
# Test webhook
curl -X POST http://localhost:8000/auth/webhook/users \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=YOUR_SIGNATURE_HERE" \
  -d '{
    "external_id": "ext_123",
    "username": "novousuario", 
    "email": "novo@example.com",
    "full_name": "Novo Usuário",
    "role": "student",
    "action": "create"
  }'

# Test login
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=adminpass"

# Test user list (requires token)
curl -X GET http://localhost:8000/auth/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## Webhook Actions

The webhook supports these actions:

- **create**: Create a new user account
- **update**: Update existing user information
- **delete**: Delete user account
- **approve**: Approve user (add to approved list or update existing user)
- **disable**: Disable user account

## Security Considerations

1. **JWT Tokens**: Expire after 180 minutes (configurable)
2. **Password Hashing**: Uses bcrypt for secure password storage
3. **Webhook Signatures**: All webhook requests must have valid HMAC signatures
4. **Role-based Access**: Different endpoints restricted by user roles
5. **User Approval**: Users must be approved to access the system

## Admin Interface Features

The admin interface (`/users`) provides:

- **User Overview**: See all users with their status, roles, and activity
- **User Creation**: Create new users with roles and approval status
- **User Management**: Enable/disable users, approve/unapprove, delete users
- **Approved Users List**: Manage the pre-approved users list for webhook sync
- **Real-time Updates**: Refresh data and see changes immediately

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Check if user is approved and not disabled
2. **Webhook Signature Invalid**: Verify the WEBHOOK_SECRET matches and signature is correct
3. **Token Expired**: Login again to get a new token
4. **Permission Denied**: Check if user has the required role for the endpoint

### Debug Endpoints

- `GET /health` - Check if backend is running
- `GET /debug` - Admin debug interface (frontend)
- Backend logs show detailed authentication and webhook processing information

### File Locations

- User database: `backend/users_db.json`
- Approved users: `backend/approved_users.json`  
- Frontend user management: `/users` (admin only)
- Backend logs: Console output when running uvicorn
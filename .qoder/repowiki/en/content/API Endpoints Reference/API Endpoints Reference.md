# API Endpoints Reference

<cite>
**Referenced Files in This Document**   
- [auth.py](file://api/auth.py)
- [users.py](file://api/users.py)
- [reports.py](file://api/reports.py)
- [files.py](file://api/files.py)
- [admin.py](file://api/admin.py)
- [config.py](file://api/config.py)
- [schemas.py](file://api/schemas.py)
- [versioning.py](file://api/versioning.py)
- [security.py](file://api/security.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Authentication Endpoints](#authentication-endpoints)
3. [User Management Endpoints](#user-management-endpoints)
4. [Report Management Endpoints](#report-management-endpoints)
5. [File Management Endpoints](#file-management-endpoints)
6. [Administrative Endpoints](#administrative-endpoints)
7. [Configuration Management Endpoints](#configuration-management-endpoints)
8. [API Versioning Strategy](#api-versioning-strategy)
9. [Rate Limiting Implementation](#rate-limiting-implementation)
10. [Security Considerations](#security-considerations)
11. [Client Integration Examples](#client-integration-examples)
12. [Pagination, Filtering, and Sorting](#pagination-filtering-and-sorting)

## Introduction
This document provides comprehensive reference documentation for the Flask-RESTX based RESTful API endpoints under /api/v1. The API supports various operations including authentication, user management, report handling, file management, administrative functions, and configuration management. All endpoints follow consistent patterns for authentication, error handling, and response formatting.

**Section sources**
- [auth.py](file://api/auth.py#L1-L429)
- [users.py](file://api/users.py#L1-L335)
- [reports.py](file://api/reports.py#L1-L503)
- [files.py](file://api/files.py#L1-L399)
- [admin.py](file://api/admin.py#L1-L23)
- [config.py](file://api/config.py#L1-L452)
- [schemas.py](file://api/schemas.py#L1-L306)
- [versioning.py](file://api/versioning.py#L1-L354)
- [security.py](file://api/security.py#L1-L576)

## Authentication Endpoints

The authentication endpoints handle user login, registration, password management, and multi-factor authentication. These endpoints use JWT tokens for stateless authentication and session-based authentication for web clients.

### Login Endpoint
**URL**: `POST /api/v1/auth/login`  
**Authentication**: None  
**Rate Limit**: 5 attempts per 5 minutes

Request body schema: `LoginSchema` from `api/schemas.py`

```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "remember_me": true,
  "mfa_token": "123456"
}
```

Successful response (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "Engineer",
    "mfa_enabled": true
  }
}
```

Error responses:
- 400: Missing email or password
- 401: Invalid credentials or MFA token
- 429: Rate limit exceeded

### Registration Endpoint
**URL**: `POST /api/v1/auth/register`  
**Authentication**: None  
**Rate Limit**: 3 registrations per hour

Request body schema: `UserRegistrationSchema` from `api/schemas.py`

```json
{
  "full_name": "Jane Smith",
  "email": "jane@example.com",
  "password": "securepassword123",
  "requested_role": "Engineer"
}
```

Successful response (201):
```json
{
  "message": "Registration successful. Account pending approval.",
  "user_id": "user-456"
}
```

Error responses:
- 400: Invalid input data
- 409: User with email already exists

### Password Change Endpoint
**URL**: `POST /api/v1/auth/password/change`  
**Authentication**: JWT or Session  
**Permissions**: Authenticated user

Request body schema: `PasswordChangeSchema` from `api/schemas.py`

```json
{
  "current_password": "oldpassword123",
  "new_password": "newsecurepassword123"
}
```

Successful response (200):
```json
{
  "message": "Password successfully changed"
}
```

Error responses:
- 400: Current password incorrect or new password validation failed
- 401: Authentication required

### MFA Setup and Verification
Endpoints for setting up and managing multi-factor authentication:

- `POST /api/v1/auth/mfa/setup` - Initiates MFA setup, returns QR code URL and backup codes
- `POST /api/v1/auth/mfa/verify` - Verifies MFA token and enables MFA
- `POST /api/v1/auth/mfa/disable` - Disables MFA after verification

**Section sources**
- [auth.py](file://api/auth.py#L1-L429)
- [schemas.py](file://api/schemas.py#L1-L306)

## User Management Endpoints

The user management endpoints allow administrators to manage user accounts, including creating, reading, updating, and deleting users, as well as approving pending registrations.

### Users List Endpoint
**URL**: `GET /api/v1/users`  
**Authentication**: JWT or Session  
**Permissions**: Admin role required  
**Response Schema**: `UserListSchema`

Query parameters:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `search`: Text search on full name or email
- `role`: Filter by user role
- `status`: Filter by status (active, inactive, pending)

Response example:
```json
{
  "users": [
    {
      "id": "user-123",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "Engineer",
      "is_active": true,
      "is_approved": true,
      "created_at": "2023-01-15T10:30:00Z",
      "last_login": "2023-01-20T14:45:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

### User Creation Endpoint
**URL**: `POST /api/v1/users`  
**Authentication**: JWT or Session  
**Permissions**: Admin role required  
**Request Schema**: `UserSchema`

```json
{
  "full_name": "New User",
  "email": "newuser@example.com",
  "role": "Engineer",
  "is_active": true,
  "is_approved": true
}
```

### User Update Endpoint
**URL**: `PUT /api/v1/users/{user_id}`  
**Authentication**: JWT or Session  
**Permissions**: Admin role or user self (limited fields)

Regular users can only update their full name, while admins can update all fields.

### User Approval and Rejection
Admin-only endpoints for managing pending user registrations:
- `POST /api/v1/users/{user_id}/approve` - Approve a pending user account
- `POST /api/v1/users/{user_id}/reject` - Reject and remove a pending user account

### Current User Profile
**URL**: `GET /api/v1/users/me`  
**Authentication**: JWT or Session  
**Permissions**: Authenticated user

Returns the current user's profile information.

**Section sources**
- [users.py](file://api/users.py#L1-L335)
- [schemas.py](file://api/schemas.py#L1-L306)

## Report Management Endpoints

The report management endpoints handle the creation, modification, approval, and generation of reports. These endpoints implement comprehensive access control and audit logging.

### Reports List Endpoint
**URL**: `GET /api/v1/reports`  
**Authentication**: JWT or Session  
**Permissions**: `reports:read` permission  
**Response Schema**: `ReportListSchema`

Query parameters:
- `page`, `per_page`: Pagination
- `search`: Full text search
- `status`: Filter by status (Draft, Pending Approval, Approved, Generated, Rejected)
- `client`: Filter by client name
- `created_by`: Filter by creator (Admin only)
- `sort_by`: Field to sort by (created_at, updated_at, document_title)
- `sort_order`: Sort order (asc, desc)

### Report Creation Endpoint
**URL**: `POST /api/v1/reports`  
**Authentication**: JWT or Session  
**Permissions**: Engineer, Admin, or Automation Manager role  
**Request Schema**: `ReportCreateSchema`

```json
{
  "document_title": "SAT Report Q1 2023",
  "document_reference": "SAT-2023-001",
  "project_reference": "PRJ-001",
  "client_name": "Acme Corporation",
  "revision": "1.0",
  "prepared_by": "John Doe",
  "date": "2023-01-15",
  "purpose": "System Acceptance Testing",
  "scope": "Testing of all system components"
}
```

### Report Submission and Approval
- `POST /api/v1/reports/{report_id}/submit` - Submit a draft report for approval
- `POST /api/v1/reports/{report_id}/approve` - Approve or reject a report (Admin or PM only)

Approval request:
```json
{
  "action": "approve",
  "comments": "Report meets all requirements"
}
```

### Report Generation
**URL**: `POST /api/v1/reports/{report_id}/generate`  
**Authentication**: JWT or Session  
**Permissions**: Authenticated user  
**Requirements**: Report must be in "Approved" status

Triggers the generation of the final report document.

**Section sources**
- [reports.py](file://api/reports.py#L1-L503)
- [schemas.py](file://api/schemas.py#L1-L306)

## File Management Endpoints

The file management endpoints handle file uploads, downloads, and management, with support for associating files with reports.

### File Upload Endpoint
**URL**: `POST /api/v1/files/upload`  
**Authentication**: JWT or Session  
**Permissions**: Authenticated user  
**Request**: Multipart form data

Form fields:
- `file`: The file to upload
- `report_id`: Optional report ID to associate the file with

Allowed file types: PNG, JPG, JPEG, GIF, PDF, DOCX, XLSX, TXT, CSV  
Maximum file size: 16MB

Successful response (201):
```json
{
  "file_id": "file-123",
  "filename": "document.pdf",
  "file_size": 15420,
  "file_type": "application/pdf",
  "upload_date": "2023-01-20T10:30:00Z",
  "url": "/api/v1/files/file-123"
}
```

### File Download Endpoint
**URL**: `GET /api/v1/files/{file_id}`  
**Authentication**: JWT or Session  
**Permissions**: Authenticated user with access to associated report

Query parameters:
- `report_id`: Required if file is associated with a report

Returns the file as an attachment.

### Files List Endpoint
**URL**: `GET /api/v1/files`  
**Authentication**: JWT or Session  
**Permissions**: Authenticated user

Query parameters:
- `page`, `per_page`: Pagination
- `report_id`: Filter by associated report

**Section sources**
- [files.py](file://api/files.py#L1-L399)
- [schemas.py](file://api/schemas.py#L1-L306)

## Administrative Endpoints

Administrative endpoints provide health checks and system monitoring capabilities for administrators.

### Admin Health Check
**URL**: `GET /api/v1/admin/health`  
**Authentication**: JWT or Session  
**Permissions**: Admin role required

Response:
```json
{
  "status": "healthy",
  "message": "Admin API is operational"
}
```

This endpoint verifies that the administrative interface is functioning correctly.

**Section sources**
- [admin.py](file://api/admin.py#L1-L23)

## Configuration Management Endpoints

The configuration management endpoints allow administrators to view, modify, and manage system configuration and secrets.

### Configuration Status
**URL**: `GET /api/v1/config/status`  
**Authentication**: JWT or Session  
**Permissions**: Admin role required  
**Response Schema**: `ConfigStatus`

Returns information about configuration sources, merged keys, and watcher status.

### Configuration Retrieval and Modification
- `GET /api/v1/config/get/{key}` - Retrieve a configuration value
- `POST /api/v1/config/set` - Set a configuration value at runtime

Set request:
```json
{
  "key": "database.connection_timeout",
  "value": 30,
  "source": "runtime"
}
```

### Configuration Export and Import
- `GET /api/v1/config/export` - Export current configuration (YAML or JSON)
- `POST /api/v1/config/validate` - Validate configuration data
- `POST /api/v1/config/reload` - Reload configuration from all sources

### Secrets Management
Endpoints for managing sensitive configuration values:
- `GET /api/v1/config/secrets` - List secret keys
- `GET /api/v1/config/secrets/{key}` - Get secret value (masked)
- `PUT /api/v1/config/secrets/{key}` - Store secret value
- `DELETE /api/v1/config/secrets/{key}` - Delete secret
- `POST /api/v1/config/secrets/{key}/rotate` - Schedule secret rotation

**Section sources**
- [config.py](file://api/config.py#L1-L452)
- [schemas.py](file://api/schemas.py#L1-L306)

## API Versioning Strategy

The API implements a comprehensive versioning strategy to ensure backward compatibility and smooth transitions between versions.

### Version Identification
Clients can specify the API version through multiple methods:
1. **Accept Header**: `Accept: application/vnd.satreportgenerator.v1+json`
2. **Custom Header**: `API-Version: 1.0.0`
3. **URL Path**: `/api/v1/` (major version only)

The system resolves the requested version to the most appropriate supported version.

### Version Management
The versioning system is implemented in `api/versioning.py` using the `VersionManager` class. Key features:

- **Supported Versions**: Currently only v1.0.0 is supported
- **Backward Compatibility**: Same major versions are backward compatible
- **Deprecation Policy**: Deprecated versions receive warning headers
- **Feature Flags**: Features can be enabled/disabled by version

### Version Headers
Responses include version-related headers:
- `API-Version`: The version used for the request
- `API-Supported-Versions`: Comma-separated list of supported versions
- `Deprecation` and `Sunset`: For deprecated versions
- `Warning`: Human-readable deprecation notice

### Version Decorators
The `@version_required` decorator enforces version constraints on endpoints:
```python
@version_required(min_version="1.0.0", max_version="1.1.0")
def my_endpoint():
    pass
```

**Section sources**
- [versioning.py](file://api/versioning.py#L1-L354)

## Rate Limiting Implementation

The API implements a sophisticated rate limiting system to prevent abuse and ensure fair usage.

### Rate Limiting Strategies
The system uses different rate limits based on authentication method:

| Authentication | Limit | Window |
|----------------|-------|--------|
| Anonymous (IP) | 100 requests | 1 hour |
| Authenticated | 1,000 requests | 1 hour |
| API Key | 5,000 requests | 1 hour |
| Admin | 10,000 requests | 1 hour |

API keys can have custom rate limits configured.

### Rate Limiting Logic
Implemented in `api/security.py` using the `RateLimiter` class:

1. **Identifier Priority**: API Key > User ID > IP Address
2. **Sliding Window**: Tracks requests within a time window
3. **IP Blocking**: Temporarily blocks IPs with excessive violations
4. **Memory Storage**: Uses in-memory deque (Redis in production)

### Rate Limit Headers
All responses include rate limiting information:
- `X-RateLimit-Limit`: Maximum requests in the window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when the counter resets (Unix timestamp)
- `Retry-After`: For 429 responses

### Rate Limit Decorator
The `@require_auth` decorator automatically applies rate limiting:

```python
@require_auth(permissions=['reports:read'])
def get_reports():
    pass
```

**Section sources**
- [security.py](file://api/security.py#L1-L576)

## Security Considerations

The API implements multiple security layers to protect data and prevent common vulnerabilities.

### Authentication Methods
Three authentication methods are supported:
1. **JWT Tokens**: Statelesss authentication for APIs
2. **Session-Based**: For web clients with CSRF protection
3. **API Keys**: For external integrations with granular permissions

### CSRF Protection
Web clients are protected against CSRF attacks:
- CSRF tokens required for state-changing operations
- Implemented in `security/validation.py`
- Configured in `static/js/csrf_manager.js`

### Token Security
JWT tokens include enhanced security features:
- Expiration (1 hour by default)
- JWT ID (jti) for potential revocation
- Issuer (iss) and Audience (aud) claims
- HMAC-SHA256 signing
- Token blacklist capability (planned)

### Input Validation
Comprehensive input validation using Marshmallow schemas:
- Field type validation
- Length constraints
- Pattern matching (regex)
- Custom validation functions
- Automatic string stripping

### Security Headers
All API responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`
- `Content-Security-Policy`
- `Referrer-Policy`

### Audit Logging
All security-relevant events are logged:
- Authentication successes and failures
- Permission denials
- Sensitive operations
- Rate limit violations
- API key usage

**Section sources**
- [security.py](file://api/security.py#L1-L576)
- [auth.py](file://api/auth.py#L1-L429)
- [security/validation.py](file://security/validation.py)

## Client Integration Examples

### Python Client Example
```python
import requests
import json

class SATReportClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers['X-API-Key'] = api_key
    
    def login(self, email, password):
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={
                "email": email,
                "password": password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.session.headers['Authorization'] = f"Bearer {data['access_token']}"
            return data
        else:
            raise Exception(f"Login failed: {response.text}")
    
    def get_reports(self, page=1, per_page=20):
        response = self.session.get(
            f"{self.base_url}/api/v1/reports",
            params={"page": page, "per_page": per_page}
        )
        return response.json()
    
    def create_report(self, report_data):
        response = self.session.post(
            f"{self.base_url}/api/v1/reports",
            json=report_data
        )
        return response.json()

# Usage
client = SATReportClient("https://api.example.com")
client.login("user@example.com", "password123")
reports = client.get_reports()
```

### JavaScript Client Example
```javascript
class SATReportAPI {
    constructor(baseUrl, apiKey = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.headers = {
            'Content-Type': 'application/json',
        };
        
        if (apiKey) {
            this.headers['X-API-Key'] = apiKey;
        }
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}/api/v1${endpoint}`;
        const config = {
            headers: { ...this.headers, ...options.headers },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        this.headers['Authorization'] = `Bearer ${data.access_token}`;
        return data;
    }
    
    async uploadFile(file, reportId = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (reportId) {
            formData.append('report_id', reportId);
        }
        
        return this.request('/files/upload', {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set content type for FormData
        });
    }
}

// Usage
const api = new SATReportAPI('https://api.example.com');
api.login('user@example.com', 'password123')
    .then(data => console.log('Logged in:', data))
    .catch(error => console.error('Login failed:', error));
```

**Section sources**
- [security.py](file://api/security.py#L1-L576)
- [auth.py](file://api/auth.py#L1-L429)

## Pagination, Filtering, and Sorting

The API implements consistent pagination, filtering, and sorting mechanisms across list endpoints.

### Pagination
All list endpoints support pagination with the following parameters:
- `page`: Page number (1-indexed, default: 1)
- `per_page`: Items per page (default: 20, maximum: 100)

Response includes pagination metadata:
```json
{
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

### Filtering
List endpoints support various filtering options:

**Text Search**: `search` parameter for full-text search across multiple fields
```http
GET /api/v1/reports?search=acme
```

**Field Filtering**: Specific parameters for exact matches
```http
GET /api/v1/reports?status=Approved&client=Acme
```

**Role-Based Access Control**: Users only see their own records unless they have admin privileges.

### Sorting
Sorting is controlled by two parameters:
- `sort_by`: Field to sort by (e.g., created_at, updated_at, document_title)
- `sort_order`: Direction (asc or desc, default: desc)

```http
GET /api/v1/reports?sort_by=created_at&sort_order=asc
```

### Consistent Response Format
All list endpoints use a consistent response structure:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

This pattern is implemented in `api/schemas.py` using the `PaginationSchema` and related classes.

**Section sources**
- [schemas.py](file://api/schemas.py#L1-L306)
- [reports.py](file://api/reports.py#L1-L503)
- [users.py](file://api/users.py#L1-L335)
- [files.py](file://api/files.py#L1-L399)
# Deployment & Configuration

<cite>
**Referenced Files in This Document**   
- [wsgi.py](file://wsgi.py)
- [run_https_443.py](file://run_https_443.py)
- [iis_web_config.xml](file://iis_web_config.xml)
- [start_production.bat](file://start_production.bat)
- [config/production.yaml](file://config/production.yaml)
- [config/development.yaml](file://config/development.yaml)
- [config/testing.yaml](file://config/testing.yaml)
- [config/app.yaml](file://config/app.yaml)
- [config/secrets.py](file://config/secrets.py)
- [config/manager.py](file://config/manager.py)
</cite>

## Table of Contents
1. [Configuration Hierarchy](#configuration-hierarchy)
2. [Secrets Management](#secrets-management)
3. [IIS Setup](#iis-setup)
4. [WSGI Configuration](#wsgi-configuration)
5. [SSL/TLS and Security Hardening](#ssltls-and-security-hardening)
6. [Environment-Specific Configuration Examples](#environment-specific-configuration-examples)
7. [Database Connection Setup](#database-connection-setup)
8. [Troubleshooting Common Deployment Issues](#troubleshooting-common-deployment-issues)

## Configuration Hierarchy

The SERVER application implements a hierarchical configuration system using YAML files to manage settings across different environments. The configuration system is managed by `config/manager.py`, which loads and merges settings from multiple sources in a defined priority order.

The configuration hierarchy follows this precedence (from lowest to highest):
1. **Default configuration** (`config/app.yaml`) - Base settings for all environments
2. **Environment-specific configuration** (`config/development.yaml`, `config/testing.yaml`, `config/production.yaml`)
3. **Local overrides** (`config/local.yaml`) - Highest priority, not committed to version control
4. **Environment variables** - Highest runtime priority, prefixed with `SAT_`

The system supports hot-reloading of configuration files, allowing changes to be applied without restarting the application. Configuration validation is performed using Marshmallow schemas to ensure structural integrity.

```mermaid
flowchart TD
A["Environment Variables<br>(SAT_* prefix)"] --> M[Merged Configuration]
B[local.yaml] --> M
C[production.yaml] --> M
D[development.yaml] --> M
E[testing.yaml] --> M
F[app.yaml] --> M
G[File System Watcher] --> H[Auto-reload on change]
```

**Diagram sources**
- [config/manager.py](file://config/manager.py#L1-L607)
- [config/app.yaml](file://config/app.yaml#L1-L126)

**Section sources**
- [config/manager.py](file://config/manager.py#L1-L607)
- [config/app.yaml](file://config/app.yaml#L1-L126)

## Secrets Management

The application uses a dual-layer secrets management system implemented in `config/secrets.py`, providing both enterprise-grade and fallback options:

1. **HashiCorp Vault Integration** - Primary secrets backend for production environments
2. **Local Encrypted Storage** - Fallback option using Fernet encryption with PBKDF2 key derivation

The `SecretsManager` class provides a unified interface that automatically falls back from Vault to local storage. Secrets can be accessed via environment variables as a last resort. The system supports automatic secret rotation, caching with TTL, and comprehensive logging.

Key features include:
- AppRole authentication for Vault
- Local encryption using Fernet with 32-byte keys
- Thread-safe operations with locking
- Automatic token renewal for Vault
- Secret expiration and access tracking
- Environment variable fallback mechanism

```mermaid
classDiagram
class SecretsManager {
+init_vault(vault_url, token)
+init_local(secrets_file, master_key)
+get_secret(key)
+put_secret(key, value)
+delete_secret(key)
+schedule_rotation(key, interval)
}
class VaultClient {
+authenticate_approle()
+get_secret(path)
+put_secret(path, data)
+delete_secret(path)
+renew_token()
}
class LocalSecretsManager {
+get_secret(key)
+put_secret(key, value)
+_get_cipher()
+_load_secrets()
+_save_secrets()
}
SecretsManager --> VaultClient : "uses"
SecretsManager --> LocalSecretsManager : "uses"
SecretsManager --> "Environment Variables" : "fallback"
```

**Diagram sources**
- [config/secrets.py](file://config/secrets.py#L1-L688)

**Section sources**
- [config/secrets.py](file://config/secrets.py#L1-L688)

## IIS Setup

The application can be deployed behind IIS using the provided `iis_web_config.xml` configuration file. This setup uses IIS as a reverse proxy to forward requests to the Flask application running on a local port.

The IIS configuration includes:
- URL rewrite rules to proxy all requests to `http://127.0.0.1:8000`
- Security headers including HSTS, XSS protection, and frame denial
- Custom error handling for 500 errors
- Forwarded headers for protocol, client IP, and original host

The `start_production.bat` script can be adapted to run the application on port 8000 for IIS proxying. The IIS site should be configured to use the provided XML configuration file in the web.config.

```mermaid
flowchart LR
A[Client] --> B[IIS Server]
B --> C{HTTPS Request}
C --> D[URL Rewrite Module]
D --> E[Flask App<br>http://127.0.0.1:8000]
E --> F[Database]
E --> G[Redis]
E --> H[File Storage]
style B fill:#4CAF50,stroke:#388E3C
style E fill:#2196F3,stroke:#1976D2
```

**Diagram sources**
- [iis_web_config.xml](file://iis_web_config.xml#L1-L37)
- [start_production.bat](file://start_production.bat#L1-L73)

**Section sources**
- [iis_web_config.xml](file://iis_web_config.xml#L1-L37)
- [start_production.bat](file://start_production.bat#L1-L73)

## WSGI Configuration

The production WSGI configuration is defined in `wsgi.py`, which uses Waitress as the production server. This configuration is optimized for performance and stability in production environments.

Key WSGI settings include:
- 6 worker threads for optimal concurrency
- Connection limit of 50 to prevent overload
- 60-second channel timeout for idle connections
- 100MB overflow buffer for large responses
- 10MB maximum request body size
- Poll-based asyncore for better performance than select()

The WSGI application creates the Flask app in production mode and serves it on all interfaces (0.0.0.0) on the specified port. This configuration should be used with process managers like systemd or Windows Services for production deployments.

```mermaid
sequenceDiagram
participant Client
participant Waitress
participant FlaskApp
participant ConfigManager
participant Database
Client->>Waitress : HTTP Request
Waitress->>Waitress : Connection management
Waitress->>FlaskApp : Forward request
FlaskApp->>ConfigManager : Get configuration
FlaskApp->>Database : Execute query
Database-->>FlaskApp : Return data
FlaskApp-->>Waitress : Generate response
Waitress-->>Client : HTTP Response
```

**Diagram sources**
- [wsgi.py](file://wsgi.py#L1-L42)

**Section sources**
- [wsgi.py](file://wsgi.py#L1-L42)

## SSL/TLS and Security Hardening

SSL/TLS configuration is handled by `run_https_443.py`, which sets up a production-ready HTTPS server. The application supports both production SSL certificates and ad-hoc self-signed certificates for development.

Security hardening measures include:
- HTTPS enforcement with SSL context
- Domain-based access control
- IP address blocking
- Secure session cookies (HttpOnly, Secure, SameSite=Strict)
- CSRF protection
- Rate limiting
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.)

The SSL certificates should be placed in the `ssl/` directory as `server.crt` and `server.key`. The application will use these certificates if present, otherwise falling back to an ad-hoc self-signed certificate.

```mermaid
flowchart TD
A[Client] --> B{HTTPS Request}
B --> C[SSL/TLS Termination]
C --> D[Domain Validation]
D --> |Valid Domain| E[Request Processing]
D --> |Invalid Domain| F[Block Request]
E --> G[Security Headers]
G --> H[CSRF Validation]
H --> I[Rate Limiting]
I --> J[Application Logic]
J --> K[Database]
K --> L[Response]
L --> M[Security Headers]
M --> N[Client]
```

**Diagram sources**
- [run_https_443.py](file://run_https_443.py#L1-L124)

**Section sources**
- [run_https_443.py](file://run_https_443.py#L1-L124)

## Environment-Specific Configuration Examples

The application provides three environment-specific configuration files that extend the base `app.yaml` configuration:

**Development Environment** (`config/development.yaml`):
- Debug mode enabled
- SQLite database with in-memory storage
- Console and file logging
- Disabled rate limiting
- 1-hour session timeout

**Testing Environment** (`config/testing.yaml`):
- Testing mode enabled
- In-memory SQLite database
- Minimal logging (ERROR level)
- All security features disabled
- No backup scheduling
- Cache disabled

**Production Environment** (`config/production.yaml`):
- PostgreSQL database recommended
- 20 connection pool size
- Redis cache integration
- File-based logging with 50MB rotation
- Strict security settings (CSRF, rate limiting)
- Daily automated backups
- Prometheus monitoring enabled

```mermaid
graph TD
A[app.yaml] --> B[development.yaml]
A --> C[testing.yaml]
A --> D[production.yaml]
B --> E["debug: true<br>database: sqlite<br>logging: DEBUG"]
C --> F["testing: true<br>database: :memory:<br>security: disabled"]
D --> G["debug: false<br>database: postgresql<br>cache: redis<br>monitoring: prometheus"]
style A fill:#FFC107,stroke:#FFA000
style B fill:#4CAF50,stroke:#388E3C
style C fill:#2196F3,stroke:#1976D2
style D fill:#F44336,stroke:#D32F2F
```

**Diagram sources**
- [config/development.yaml](file://config/development.yaml#L1-L50)
- [config/testing.yaml](file://config/testing.yaml#L1-L53)
- [config/production.yaml](file://config/production.yaml#L1-L84)

**Section sources**
- [config/development.yaml](file://config/development.yaml#L1-L50)
- [config/testing.yaml](file://config/testing.yaml#L1-L53)
- [config/production.yaml](file://config/production.yaml#L1-L84)

## Database Connection Setup

Database configuration is managed through the hierarchical YAML configuration system. The default configuration in `app.yaml` uses SQLite, but production deployments should use PostgreSQL.

**Development Database**:
```yaml
database:
  uri: "sqlite:///instance/dev.db"
  pool_size: 5
  pool_timeout: 30
  pool_recycle: 3600
```

**Production Database**:
```yaml
database:
  uri: "postgresql://user:password@localhost/sat_reports"
  pool_size: 20
  pool_timeout: 30
  pool_recycle: 3600
```

The database connection pool settings are critical for production performance:
- `pool_size`: Number of connections to maintain in the pool
- `pool_timeout`: Timeout for getting a connection from the pool
- `pool_recycle`: Time before connections are recycled to prevent staleness

Connection credentials should be stored in secrets management rather than configuration files. The application will automatically use secrets from Vault or local encrypted storage when available.

```mermaid
flowchart LR
A[Application] --> B[Connection Pool]
B --> C[Active Connection 1]
B --> D[Active Connection 2]
B --> E[Active Connection N]
C --> F[PostgreSQL]
D --> F
E --> F
style B fill:#9C27B0,stroke:#7B1FA2
style F fill:#009688,stroke:#00796B
```

**Section sources**
- [config/app.yaml](file://config/app.yaml#L1-L126)
- [config/production.yaml](file://config/production.yaml#L1-L84)

## Troubleshooting Common Deployment Issues

### Permission Errors
**Symptoms**: "Permission denied for port 443" or access denied to files
**Solutions**:
- Run the application as administrator when using ports < 1024
- Ensure the application has write permissions to log, upload, and instance directories
- Verify SSL certificate files have appropriate read permissions

### Missing Dependencies
**Symptoms**: Module not found errors or import failures
**Solutions**:
- Install dependencies from requirements.txt: `pip install -r requirements.txt`
- Verify Python version compatibility (3.7+ recommended)
- Check that all required system libraries are installed

### Port Conflicts
**Symptoms**: "Address already in use" or connection refused
**Solutions**:
- Check for existing processes using the port: `netstat -ano | findstr :<port>`
- Change the application port in configuration or environment variables
- Use IIS or nginx as a reverse proxy on port 80/443

### SSL/TLS Issues
**Symptoms**: SSL errors or certificate warnings
**Solutions**:
- Ensure SSL certificates are in the correct format (PEM)
- Verify certificate chain is complete
- Check that private key is not password-protected
- Ensure certificate and key files are in the `ssl/` directory

### Database Connection Problems
**Symptoms**: Database connection timeouts or authentication failures
**Solutions**:
- Verify database server is running and accessible
- Check connection string format and credentials
- Ensure database user has appropriate permissions
- Verify network connectivity and firewall rules

**Section sources**
- [run_https_443.py](file://run_https_443.py#L1-L124)
- [start_production.bat](file://start_production.bat#L1-L73)
- [wsgi.py](file://wsgi.py#L1-L42)
- [config/production.yaml](file://config/production.yaml#L1-L84)
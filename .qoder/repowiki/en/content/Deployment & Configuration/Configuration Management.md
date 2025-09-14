# Configuration Management

<cite>
**Referenced Files in This Document**   
- [config/manager.py](file://config/manager.py)
- [config/secrets.py](file://config/secrets.py)
- [config/app.yaml](file://config/app.yaml)
- [config/development.yaml](file://config/development.yaml)
- [config/production.yaml](file://config/production.yaml)
- [config/testing.yaml](file://config/testing.yaml)
- [app.py](file://app.py)
- [config.py](file://config.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Configuration Hierarchy and File Structure](#configuration-hierarchy-and-file-structure)
3. [Core Configuration Manager](#core-configuration-manager)
4. [Base Configuration: app.yaml](#base-configuration-appyaml)
5. [Environment-Specific Configuration](#environment-specific-configuration)
6. [Secrets Management System](#secrets-management-system)
7. [Configuration Loading and Merging Process](#configuration-loading-and-merging-process)
8. [Practical Configuration Examples](#practical-configuration-examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting Guide](#troubleshooting-guide)

## Introduction
The SERVER application implements a hierarchical configuration management system that enables flexible, environment-aware settings management. This system combines YAML-based configuration files with runtime environment variables and secure secrets management to provide a robust configuration framework. The architecture supports development, testing, and production environments with appropriate security and performance characteristics for each. The system is designed to prevent secrets leakage, support hot-reloading of configuration changes, and validate configuration integrity through schema validation.

## Configuration Hierarchy and File Structure
The configuration system follows a hierarchical structure with multiple layers of configuration sources that are merged in priority order. The system is organized around environment-specific YAML files located in the `config/` directory, with a clear precedence hierarchy that determines which values take priority when conflicts occur.

```mermaid
graph TD
A[Environment Variables] --> |Highest Priority| B[local.yaml]
B --> C[production.yaml]
C --> D[development.yaml]
D --> E[testing.yaml]
E --> F[app.yaml]
F --> |Lowest Priority| G[Default Values]
```

**Diagram sources**
- [config/manager.py](file://config/manager.py#L500-L550)
- [config/app.yaml](file://config/app.yaml#L1-L10)

**Section sources**
- [config/manager.py](file://config/manager.py#L1-L100)
- [config/app.yaml](file://config/app.yaml#L1-L20)

## Core Configuration Manager
The `HierarchicalConfigManager` class in `config/manager.py` serves as the central component of the configuration system, responsible for loading, merging, validating, and providing access to configuration data from multiple sources. The manager implements a thread-safe, hierarchical approach to configuration management with support for hot-reloading when configuration files are modified.

```mermaid
classDiagram
class HierarchicalConfigManager {
+base_path : Path
+sources : List[ConfigSource]
+merged_config : Dict[str, Any]
+validation_schema : ConfigValidationSchema
+observers : List[Observer]
+lock : RLock
+reload_callbacks : List[callable]
+add_source(name, path, priority) : ConfigSource
+merge_configurations() : Dict[str, Any]
+validate_configuration(config) : Dict[str, Any]
+reload_configuration(changed_file) : void
+get(key, default) : Any
+set(key, value, source_name) : void
+start_file_watching() : void
+stop_file_watching() : void
}
class ConfigSource {
+name : str
+path : Optional[str]
+priority : int
+last_modified : Optional[datetime]
+data : Dict[str, Any]
+is_valid : bool
+error_message : Optional[str]
}
class ConfigValidationSchema {
+app_name : Str
+port : Int
+debug : Bool
+environment : Str
+secret_key : Str
+session_timeout : Int
+csrf_enabled : Bool
+database : Dict
+email : Dict
+uploads : Dict
+logging : Dict
+features : Dict
}
class ConfigFileWatcher {
+config_manager : HierarchicalConfigManager
+debounce_time : float
+last_reload : Dict
+on_modified(event) : void
}
HierarchicalConfigManager --> ConfigSource : "has many"
HierarchicalConfigManager --> ConfigValidationSchema : "uses"
HierarchicalConfigManager --> ConfigFileWatcher : "uses"
ConfigFileWatcher --> HierarchicalConfigManager : "notifies"
```

**Diagram sources**
- [config/manager.py](file://config/manager.py#L100-L300)
- [config/manager.py](file://config/manager.py#L350-L400)

**Section sources**
- [config/manager.py](file://config/manager.py#L1-L607)

## Base Configuration: app.yaml
The `app.yaml` file serves as the foundation of the configuration system, containing default values for all application settings. This base configuration is designed to work in most environments and provides sensible defaults for development, while requiring environment-specific overrides for production deployment.

```mermaid
flowchart TD
A[app.yaml] --> B[Application Settings]
A --> C[Database Configuration]
A --> D[Email Configuration]
A --> E[File Upload Settings]
A --> F[Session Configuration]
A --> G[Security Settings]
A --> H[Logging Configuration]
A --> I[Feature Flags]
A --> J[API Configuration]
A --> K[Monitoring Settings]
A --> L[Backup Configuration]
A --> M[Cache Configuration]
B --> B1[app_name: "SAT Report Generator"]
B --> B2[port: 5000]
B --> B3[debug: false]
B --> B4[environment: "development"]
C --> C1[uri: "sqlite:///instance/database.db"]
C --> C2[pool_size: 10]
C --> C3[pool_timeout: 30]
C --> C4[pool_recycle: 3600]
D --> D1[smtp_server: "smtp.gmail.com"]
D --> D2[smtp_port: 587]
D --> D3[use_tls: true]
E --> E1[max_file_size: 16777216]
E --> E2[allowed_extensions: png,jpg,jpeg,gif,pdf,docx]
E --> E3[upload_path: "static/uploads"]
F --> F1[timeout: 1800]
F --> F2[cookie_secure: false]
F --> F3[cookie_httponly: true]
F --> F4[cookie_samesite: "Lax"]
G --> G1[csrf_enabled: true]
G --> G2[rate_limiting.enabled: true]
H --> H1[level: "INFO"]
H --> H2[max_bytes: 10485760]
H --> H3[backup_count: 5]
I --> I1[email_notifications: true]
I --> I2[pdf_export: false]
I --> I3[api_enabled: true]
I --> I4[metrics_enabled: true]
```

**Diagram sources**
- [config/app.yaml](file://config/app.yaml#L1-L126)

**Section sources**
- [config/app.yaml](file://config/app.yaml#L1-L126)

## Environment-Specific Configuration
The configuration system supports environment-specific overrides through dedicated YAML files for development, testing, and production environments. These files contain only the settings that differ from the base configuration, following the principle of minimal override to maintain clarity and reduce duplication.

```mermaid
graph TD
subgraph Development
dev[development.yaml]
dev_debug[debug: true]
dev_db[database.uri: "sqlite:///instance/dev.db"]
dev_logging[logging.level: "DEBUG"]
dev_csrf[security.csrf_enabled: false]
dev_features[features.email_notifications: false]
end
subgraph Production
prod[production.yaml]
prod_debug[debug: false]
prod_db[database.uri: "postgresql://user:password@localhost/sat_reports"]
prod_security[security.csrf_enabled: true]
prod_logging[logging.level: "WARNING"]
prod_ssl[ssl.enabled: true]
prod_cache[cache.type: "redis"]
end
subgraph Testing
test[testing.yaml]
test_db[database.uri: "sqlite:///:memory:"]
test_csrf[security.csrf_enabled: false]
test_logging[logging.level: "ERROR"]
test_features[features.email_notifications: false]
test_monitoring[monitoring.enabled: false]
end
app[app.yaml] --> dev
app --> prod
app --> test
```

**Diagram sources**
- [config/development.yaml](file://config/development.yaml#L1-L50)
- [config/production.yaml](file://config/production.yaml#L1-L84)
- [config/testing.yaml](file://config/testing.yaml#L1-L53)

**Section sources**
- [config/development.yaml](file://config/development.yaml#L1-L50)
- [config/production.yaml](file://config/production.yaml#L1-L84)
- [config/testing.yaml](file://config/testing.yaml#L1-L53)

## Secrets Management System
The secrets management system, implemented in `config/secrets.py`, provides secure handling of sensitive data such as database passwords, API keys, and authentication tokens. The system supports multiple backends including HashiCorp Vault for production environments and encrypted local storage for development, with environment variables as a fallback option.

```mermaid
classDiagram
class SecretsManager {
+vault_client : Optional[VaultClient]
+local_manager : Optional[LocalSecretsManager]
+cache : Dict[str, Any]
+cache_ttl : Dict[str, datetime]
+rotation_schedule : Dict[str, datetime]
+rotation_thread : Optional[Thread]
+rotation_enabled : bool
+init_vault(vault_url, vault_token, ...) : void
+init_local(secrets_file, master_key) : void
+get_secret(key, use_cache) : Optional[Any]
+put_secret(key, value, backend) : bool
+delete_secret(key, backend) : bool
+list_secrets(backend) : List[str]
+schedule_rotation(key, rotation_interval) : void
+start_rotation_service() : void
+stop_rotation_service() : void
+clear_cache() : void
}
class VaultClient {
+vault_url : str
+vault_token : str
+vault_role_id : str
+vault_secret_id : str
+session : Session
+token_expires_at : Optional[datetime]
+lock : Lock
+set_token(token) : void
+authenticate_approle() : void
+is_token_valid() : bool
+renew_token() : void
+get_secret(path, version) : Optional[Dict]
+put_secret(path, data) : bool
+delete_secret(path) : bool
+list_secrets(path) : List[str]
}
class LocalSecretsManager {
+secrets_file : Path
+master_key : str
+secrets_cache : Dict[str, Any]
+metadata_cache : Dict[str, SecretMetadata]
+lock : Lock
+cipher : Fernet
+_generate_master_key() : str
+_get_cipher() : Fernet
+_load_secrets() : void
+_save_secrets() : void
+get_secret(key) : Optional[Any]
+put_secret(key, value, expires_at) : bool
+delete_secret(key) : bool
+list_secrets() : List[str]
}
class SecretMetadata {
+key : str
+version : int
+created_at : Optional[datetime]
+expires_at : Optional[datetime]
+last_accessed : Optional[datetime]
+access_count : int
+source : str
+encrypted : bool
}
SecretsManager --> VaultClient : "uses"
SecretsManager --> LocalSecretsManager : "uses"
SecretsManager --> SecretMetadata : "manages"
LocalSecretsManager --> SecretMetadata : "contains"
```

**Diagram sources**
- [config/secrets.py](file://config/secrets.py#L100-L400)
- [config/secrets.py](file://config/secrets.py#L450-L500)

**Section sources**
- [config/secrets.py](file://config/secrets.py#L1-L688)

## Configuration Loading and Merging Process
The configuration loading process follows a well-defined sequence that ensures consistent behavior across different environments. The system initializes with the base configuration, applies environment-specific overrides, and finally incorporates environment variables for maximum flexibility.

```mermaid
sequenceDiagram
participant App as "Application"
participant Config as "HierarchicalConfigManager"
participant Files as "Configuration Files"
participant Env as "Environment Variables"
App->>Config : init_config_system(app, config_dir)
Config->>Config : create_default_configs()
Config->>Files : Load app.yaml
Config->>Files : Load {env}.yaml
Config->>Files : Load local.yaml (if exists)
Config->>Env : Load SAT_* environment variables
Config->>Config : merge_configurations()
Config->>Config : validate_configuration()
Config->>Config : start_file_watching()
Config->>App : Add reload callback
App->>App : Store config_manager in app
Config-->>App : Return config_manager
```

**Diagram sources**
- [config/manager.py](file://config/manager.py#L500-L550)
- [app.py](file://app.py#L50-L100)

**Section sources**
- [config/manager.py](file://config/manager.py#L500-L550)
- [app.py](file://app.py#L50-L100)

## Practical Configuration Examples
The configuration system supports various practical use cases for setting critical application parameters. These examples demonstrate how to configure database connections, feature flags, and API keys across different environments.

```mermaid
flowchart TD
A[Database Configuration] --> A1[Development: SQLite]
A --> A2[Production: PostgreSQL]
A --> A3[Testing: In-memory]
B[Feature Flags] --> B1[Development: PDF export enabled]
B --> B2[Production: Email notifications enabled]
B --> B3[Testing: All features minimal]
C[API Keys] --> C1[Stored in Vault]
C1 --> C1a[Accessed via secrets_manager]
C1 --> C1b[Environment variable fallback]
D[Email Configuration] --> D1[Development: TLS enabled, no auth]
D --> D2[Production: Full authentication]
D --> D3[Testing: Disabled]
E[Security Settings] --> E1[Development: CSRF disabled]
E --> E2[Production: Strict CSRF, HTTPS]
E --> E3[Testing: Security disabled]
F[Monitoring] --> F1[Development: Enabled]
F --> F2[Production: Prometheus enabled]
F --> F3[Testing: Disabled]
```

**Diagram sources**
- [config/development.yaml](file://config/development.yaml#L1-L50)
- [config/production.yaml](file://config/production.yaml#L1-L84)
- [config/testing.yaml](file://config/testing.yaml#L1-L53)
- [config/app.yaml](file://config/app.yaml#L1-L126)

**Section sources**
- [config/development.yaml](file://config/development.yaml#L1-L50)
- [config/production.yaml](file://config/production.yaml#L1-L84)
- [config/testing.yaml](file://config/testing.yaml#L1-L53)

## Best Practices
Adhering to best practices ensures secure, maintainable, and reliable configuration management across the application lifecycle.

### Configuration Organization
- **Use minimal overrides**: Only specify settings in environment files that differ from the base configuration
- **Avoid duplication**: Leverage the hierarchical nature of the system to inherit common settings
- **Document overrides**: Include comments explaining why specific values are overridden
- **Use consistent naming**: Follow the same structure and naming conventions across all configuration files

### Secrets Management
- **Never commit secrets**: Ensure sensitive data is never stored in version control
- **Use environment variables for deployment**: Set secrets via environment variables in production
- **Rotate credentials regularly**: Implement automatic secret rotation for enhanced security
- **Limit access**: Restrict access to secrets based on the principle of least privilege
- **Use Vault in production**: Always use HashiCorp Vault or equivalent for production secrets

### Validation and Testing
- **Validate configuration**: Use schema validation to catch errors early
- **Test configuration changes**: Verify configuration updates in staging before production
- **Monitor configuration changes**: Track and audit configuration modifications
- **Implement rollback**: Have a strategy for reverting problematic configuration changes
- **Document configuration**: Maintain up-to-date documentation of all configuration options

### Performance Considerations
- **Minimize file watches**: Only watch necessary configuration files
- **Cache configuration access**: Use the built-in caching mechanisms
- **Avoid frequent reloads**: Batch configuration changes when possible
- **Optimize merge operations**: Keep configuration files focused and minimal
- **Monitor configuration performance**: Track the impact of configuration on application startup

**Section sources**
- [config/manager.py](file://config/manager.py#L1-L607)
- [config/secrets.py](file://config/secrets.py#L1-L688)

## Troubleshooting Guide
Common configuration issues and their solutions are documented to assist with rapid diagnosis and resolution.

### Missing Environment Variables
**Symptoms**: Application fails to start or certain features don't work
**Diagnosis**: Check logs for "environment variable not found" messages
**Solution**: 
1. Verify required environment variables are set
2. Check for typos in variable names (case-sensitive)
3. Ensure variables are available in the execution environment
4. Use the `init_config_system` function to provide defaults

### Incorrect YAML Syntax
**Symptoms**: Configuration fails to load, parser errors in logs
**Common issues**:
- Improper indentation (YAML is indentation-sensitive)
- Missing colons after keys
- Unquoted strings with special characters
- Incorrect list formatting

**Validation**: Use online YAML validators or command-line tools like `yamllint`

### Unexpected Configuration Overrides
**Symptoms**: Settings don't match expectations despite correct configuration files
**Diagnosis**:
1. Check the configuration precedence order
2. Verify environment variables aren't overriding file settings
3. Use `config_manager.get_status()` to inspect loaded sources
4. Check for multiple configuration files being loaded

**Solution**: 
- Review the priority order in `add_source()` calls
- Use `export_config()` to see the final merged configuration
- Temporarily disable environment variable loading for debugging

### Secrets Not Loading
**Symptoms**: Authentication failures, connection errors to external services
**Diagnosis**:
1. Check if Vault is accessible
2. Verify Vault credentials and permissions
3. Check local secrets file permissions
4. Verify environment variable names

**Solution**:
- Test Vault connectivity independently
- Verify AppRole credentials
- Check master key for local encryption
- Use `secrets_manager.get_status()` to diagnose issues

### Configuration Hot-Reload Issues
**Symptoms**: Changes to configuration files don't take effect
**Diagnosis**:
1. Verify file watching is enabled
2. Check file permissions
3. Verify the correct directory is being watched
4. Check for debounce timing issues

**Solution**:
- Ensure `start_file_watching()` is called
- Verify the config directory path
- Check for file system limitations
- Review debounce settings in `ConfigFileWatcher`

**Section sources**
- [config/manager.py](file://config/manager.py#L400-L500)
- [config/secrets.py](file://config/secrets.py#L600-L650)
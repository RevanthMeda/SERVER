# Developer Setup Guide

<cite>
**Referenced Files in This Document**   
- [init_new_db.py](file://init_new_db.py)
- [run_local_https.py](file://run_local_https.py)
- [debug_start.bat](file://debug_start.bat)
- [manage_db.py](file://manage_db.py)
- [simple_migration.py](file://simple_migration.py)
- [config/development.yaml](file://config/development.yaml)
- [config/production.yaml](file://config/production.yaml)
- [config/testing.yaml](file://config/testing.yaml)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Python Environment and Dependency Setup](#python-environment-and-dependency-setup)
3. [Database Configuration and Initialization](#database-configuration-and-initialization)
4. [Running the Server Locally](#running-the-server-locally)
5. [IDE Setup and Debugging Configuration](#ide-setup-and-debugging-configuration)
6. [Database Migration Management](#database-migration-management)
7. [Environment Variables and Configuration Profiles](#environment-variables-and-configuration-profiles)
8. [Troubleshooting Common Setup Issues](#troubleshooting-common-setup-issues)

## Introduction
This guide provides comprehensive instructions for setting up a local development environment for the SERVER application. It covers dependency installation, database initialization, server execution, IDE configuration, migration management, and environment configuration. The goal is to enable developers to quickly bootstrap the application and begin contributing with minimal friction.

## Python Environment and Dependency Setup

To set up the Python environment for the SERVER application, follow these steps:

1. **Install Python 3.9 or higher**  
   Ensure Python is installed and available in your system PATH. Verify with:
   ```bash
   python --version
   ```

2. **Create a Virtual Environment**  
   Navigate to the project root and create an isolated environment:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**  
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install Dependencies**  
   Install required packages based on your development needs:
   - For full development: `[requirements-complete.txt](file://requirements-complete.txt)`
   - For minimal setup: `[requirements-minimal.txt](file://requirements-minimal.txt)`
   - For testing: `[requirements-test.txt](file://requirements-test.txt)`

   Example installation:
   ```bash
   pip install -r requirements-complete.txt
   ```

5. **Install Development Tools**  
   The project includes scripts for code quality and technical debt tracking located in the `[scripts](file://scripts)` directory. Install additional linting and formatting tools as needed.

**Section sources**
- [requirements-complete.txt](file://requirements-complete.txt)
- [requirements-minimal.txt](file://requirements-minimal.txt)
- [requirements-test.txt](file://requirements-test.txt)
- [pyproject.toml](file://pyproject.toml)

## Database Configuration and Initialization

The application uses a configurable database backend via the `DATABASE_URL` environment variable.

### Step 1: Configure Environment Variables
Create a `.env` file in the project root with:
```
DATABASE_URL=postgresql://user:password@localhost:5432/sat_report_dev
```
Supported databases include PostgreSQL, MySQL, and SQLite (for development only).

### Step 2: Initialize the Database
Use the `[init_new_db.py](file://init_new_db.py)` script to create tables and an admin user:

```bash
python init_new_db.py
```

This script performs the following:
- Validates the `.env` file and `DATABASE_URL`
- Establishes a database connection
- Creates all required tables using `db.create_all()`
- Seeds the database with an initial admin user

Admin credentials created:
- **Email**: admin@cullyautomation.com
- **Password**: admin123

**Important**: Change the password after first login.

### Step 3: Verify Initialization
Run the status command via `[manage_db.py](file://manage_db.py)` to confirm successful setup:
```bash
python manage_db.py status
```

**Section sources**
- [init_new_db.py](file://init_new_db.py#L1-L101)
- [models.py](file://models.py)
- [app.py](file://app.py)

## Running the Server Locally

You can run the server using either Python scripts or batch files with hot reloading support.

### Option 1: Using run_local_https.py (Recommended for IIS Integration)
This script configures HTTPS on port 443 and supports iframe embedding:

```bash
python run_local_https.py
```

Key features:
- Runs on `https://localhost:443` or configured domain
- Enables CORS and frame-ancestors for IIS integration
- Uses ad-hoc SSL certificates (replace with proper certs in production)
- Sets production-like environment variables

**Section sources**
- [run_local_https.py](file://run_local_https.py#L1-L121)

### Option 2: Using debug_start.bat (Windows Development)
For Windows developers, use the batch script for debugging:

```bash
debug_start.bat
```

This script:
- Validates the presence of `app.py`
- Checks Python installation
- Displays current environment variables
- Starts the Flask application with default settings

You can modify this script to include custom environment variables or debugging flags.

**Section sources**
- [debug_start.bat](file://debug_start.bat#L1-L38)
- [app.py](file://app.py)

## IDE Setup and Debugging Configuration

### Recommended IDE: VS Code or PyCharm
#### VS Code Configuration
Create a `.vscode/launch.json` file:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Flask App",
            "type": "python",
            "request": "launch",
            "program": "app.py",
            "envFile": "${workspaceFolder}/.env",
            "python": "${workspaceFolder}/venv/bin/python",
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

#### PyCharm Configuration
1. Set interpreter to virtual environment
2. Create a new run configuration:
   - Script path: `app.py`
   - Environment variables: Load from `.env` file
   - Working directory: Project root
3. Enable "Attach to subprocess automatically" for hot reloading

### Debugging Tips
- Set breakpoints in route handlers (`[routes/](file://routes/)`)
- Use Flask’s built-in debugger when `debug=True`
- Inspect database state via `[models.py](file://models.py)`
- Monitor logs in `[monitoring/logging_config.py](file://monitoring/logging_config.py)`

**Section sources**
- [app.py](file://app.py)
- [routes/main.py](file://routes/main.py)
- [monitoring/logging_config.py](file://monitoring/logging_config.py)

## Database Migration Management

The project includes two migration tools: `[manage_db.py](file://manage_db.py)` (advanced) and `[simple_migration.py](file://simple_migration.py)` (basic).

### Using manage_db.py (Recommended)
This CLI tool provides full migration lifecycle management.

#### Initialize Migrations
```bash
python manage_db.py init-migrations --env=development
```

#### Create a New Migration
```bash
python manage_db.py create-migration -m "Add report status field" --env=development
```

#### Upgrade Database
```bash
python manage_db.py upgrade --env=development
```

#### Downgrade to Specific Revision
```bash
python manage_db.py downgrade -r abc123def456 --env=development
```

#### Backup and Restore
```bash
python manage_db.py backup
python manage_db.py restore -f backups/db_backup_20250913.sql
```

#### Check Status
```bash
python manage_db.py status
```

### Using simple_migration.py (Legacy)
For simple schema changes, this script applies migrations directly:
```bash
python simple_migration.py
```

Ensure migration SQL files are placed in the correct directory before execution.

**Section sources**
- [manage_db.py](file://manage_db.py#L1-L379)
- [simple_migration.py](file://simple_migration.py)
- [database/migration_manager.py](file://database/migration_manager.py)

## Environment Variables and Configuration Profiles

The application supports multiple configuration profiles via YAML files in `[config/](file://config/)`.

### Available Profiles
- `[development.yaml](file://config/development.yaml)` – Local development
- `[testing.yaml](file://config/testing.yaml)` – Test environment
- `[production.yaml](file://config/production.yaml)` – Production settings

### Key Environment Variables
| Variable | Purpose | Example |
|--------|--------|--------|
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@localhost:5432/app_dev` |
| `FLASK_ENV` | Application environment | `development` |
| `SECRET_KEY` | Cryptographic key for sessions | `change-this-in-production` |
| `PORT` | Server port | `8080` |
| `SMTP_SERVER` | Email server address | `smtp.gmail.com` |
| `ALLOWED_DOMAINS` | Domains allowed for access | `localhost,127.0.0.1` |

### Switching Profiles
Pass the environment name to `create_app()`:
```python
app = create_app('production')
```

Or set `FLASK_ENV`:
```bash
export FLASK_ENV=production
python app.py
```

**Section sources**
- [config/development.yaml](file://config/development.yaml)
- [config/production.yaml](file://config/production.yaml)
- [config/testing.yaml](file://config/testing.yaml)
- [config/manager.py](file://config/manager.py)

## Troubleshooting Common Setup Issues

### Port Already in Use
**Symptom**: `OSError: [Errno 98] Address already in use`  
**Solution**:
- Identify process using the port:
  ```bash
  lsof -i :8080  # macOS/Linux
  netstat -ano | findstr :8080  # Windows
  ```
- Terminate the process or change the port in environment variables.

### Missing Module Errors
**Symptom**: `ModuleNotFoundError: No module named 'xxx'`  
**Solution**:
- Ensure virtual environment is activated
- Reinstall dependencies:
  ```bash
  pip install -r requirements-complete.txt
  ```
- Verify package names in `[requirements.txt](file://requirements.txt)`

### Database Connection Failed
**Symptom**: `Connection refused` or `FATAL: database does not exist`  
**Solution**:
- Confirm database server is running
- Verify `DATABASE_URL` format and credentials
- For PostgreSQL, ensure the target database exists:
  ```sql
  CREATE DATABASE sat_report_dev;
  ```

### Admin User Creation Fails
**Symptom**: Script runs but no user created  
**Solution**:
- Check if user already exists by querying the database
- Ensure `init_new_db.py` runs within app context
- Validate database permissions

### SSL Certificate Errors in HTTPS Mode
**Symptom**: Browser warnings when using `run_local_https.py`  
**Solution**:
- Accept the self-signed certificate for development
- Or generate a proper certificate and update `ssl_context` parameter

### Migration Conflicts
**Symptom**: Migration fails due to schema drift  
**Solution**:
- Run `python manage_db.py validate-schema` to detect inconsistencies
- Backup database before attempting repair
- Use `python manage_db.py analyze-performance` to identify bottlenecks

**Section sources**
- [init_new_db.py](file://init_new_db.py)
- [run_local_https.py](file://run_local_https.py)
- [manage_db.py](file://manage_db.py)
- [config/manager.py](file://config/manager.py)
- [app.py](file://app.py)
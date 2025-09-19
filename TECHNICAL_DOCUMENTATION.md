# SAT Report Generator - Technical Documentation

## System Architecture

The SAT Report Generator is a Flask-based web application designed to streamline the creation, management, and approval of various technical reports, with a primary focus on Site Acceptance Testing (SAT) reports.

### Core Components

1. **Web Application (Flask)**
   - Handles HTTP requests, routing, and view rendering
   - Manages user sessions and authentication
   - Coordinates between different system components

2. **Database Layer (SQLAlchemy)**
   - Stores user data, report content, and system settings
   - Manages relationships between different data entities
   - Provides query capabilities for report filtering and search

3. **Document Processing Engine**
   - Generates formatted reports in various formats (DOCX, PDF)
   - Processes templates with user-provided data
   - Handles image and attachment inclusion

4. **Authentication System**
   - Manages user registration, login, and session tracking
   - Implements role-based access control
   - Secures API endpoints and sensitive operations

5. **Caching System**
   - Improves performance for frequently accessed data
   - Reduces database load for common queries
   - Configurable based on environment (development/production)

## Page Linkages and Navigation Flows

### Main Navigation Paths

1. **Authentication Flow**
   - `/auth/welcome` → Welcome page with registration and login options
   - `/auth/register` → User registration form
   - `/auth/login` → User login form
   - `/auth/logout` → User logout (redirects to welcome)

2. **Dashboard Flow (Role-Based)**
   - `/dashboard/` → Role-based redirect to appropriate dashboard
   - `/dashboard/admin` → Administrator dashboard
   - `/dashboard/engineer` → Engineer dashboard
   - `/dashboard/automation_manager` → Automation Manager dashboard
   - `/dashboard/pm` → Project Manager dashboard

3. **Report Creation Flow**
   - `/reports/new` → Select report type
   - `/reports/sat/wizard` → SAT report creation wizard
   - `/reports/sat/preview/<id>` → Preview generated SAT report
   - `/reports/sat/submit/<id>` → Submit report for approval

4. **Report Management Flow**
   - `/reports/my` → List user's reports
   - `/reports/view/<id>` → View specific report
   - `/reports/download/<id>` → Download report as PDF/DOCX
   - `/reports/archive/<id>` → Archive report

5. **Approval Flow**
   - `/approval/pending` → List reports pending approval
   - `/approval/review/<id>` → Review specific report
   - `/approval/approve/<id>` → Approve report
   - `/approval/reject/<id>` → Reject report with comments

6. **Edit Flow**
   - `/edit/report/<id>` → Edit existing report
   - `/edit/save/<id>` → Save edited report

## Component Interfaces

### Database Models and Relationships

1. **User Model**
   - Core user information and authentication data
   - Role-based permissions (Admin, Engineer, Automation Manager, PM)
   - Status tracking (Pending, Active, Disabled)

2. **Report Model**
   - Base report information (common across all report types)
   - One-to-one relationships with specific report types:
     - SATReport
     - FDSReport
     - HDSReport
     - SiteSurveyReport
     - SDSReport
     - FATReport

3. **Notification System**
   - User notifications for report status changes
   - Approval requests and responses
   - System announcements

4. **Template System**
   - Report templates with versioning
   - Field specifications for different report types
   - Reusable components across reports

### API Endpoints

1. **RESTful API (`/api/v1/`)**
   - Report management endpoints
   - User management endpoints
   - File upload/download endpoints
   - Search and filtering endpoints

2. **Legacy API (to be deprecated)**
   - Backward compatibility endpoints
   - Limited functionality compared to RESTful API

## Call Hierarchy and Dependencies

### Application Initialization

1. `create_app()` in app.py
   - Configures application settings
   - Initializes extensions (SQLAlchemy, Login Manager, etc.)
   - Registers blueprints for different routes
   - Sets up error handlers and middleware

2. Database Initialization
   - `init_db()` in models.py
   - Creates database tables if they don't exist
   - Validates schema consistency

3. Blueprint Registration
   - Routes are organized into logical blueprints:
     - auth_bp: Authentication routes
     - dashboard_bp: Dashboard routes
     - reports_bp: Report management routes
     - notifications_bp: Notification routes
     - approval_bp: Approval workflow routes
     - edit_bp: Report editing routes

### Request Processing Flow

1. Request received by Flask application
2. Middleware processing (CSRF protection, session validation)
3. Route handling by appropriate blueprint
4. Database operations via SQLAlchemy models
5. Template rendering or API response generation
6. Response returned to client

## Component Relationships

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Web Interface  │────▶│  Flask Routes   │────▶│  Database Layer │
│  (HTML/CSS/JS)  │     │  (Blueprints)   │     │  (SQLAlchemy)   │
│                 │◀────│                 │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │  ▲                     │  ▲
                               │  │                     │  │
                               ▼  │                     ▼  │
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Authentication │◀───▶│  Business Logic │◀───▶│  Document       │
│  System         │     │  (Services)     │     │  Processing     │
│                 │     │                 │     │  Engine         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │  ▲
                               │  │
                               ▼  │
                        ┌─────────────────┐
                        │                 │
                        │  Caching System │
                        │  (Redis)        │
                        │                 │
                        └─────────────────┘
```

## Redundant or Obsolete Files

The following files appear to be redundant or obsolete and could potentially be safely removed:

1. `routes/dashboard_optimized.py` - Experimental optimization of dashboard routes that hasn't been integrated
2. `test_edit_functionality.py` - Test script that should be moved to the tests directory
3. `EDIT_FEATURE_FIX_SUMMARY.md` - Documentation of fixes that have already been implemented
4. `scripts/debt_dashboard.py` - Development tool not needed in production
5. `scripts/technical_debt_tracker.py` - Development utility for tracking technical debt
6. `4.0.0` - Temporary pip installation log file
7. `attached_assets/Pasted-E-report-generator-SERVER-python-app-py-Initializing-SAT-Report-Generator-2025-09-13-11-29-1757762970194_1757762970195.txt` - Debug log file that should be moved to logs directory
8. `utils.py` (lines 1247-1255) - Contains redundant duplicate functions that should be refactored

## Version Control Measures

To maintain version integrity during documentation updates:

1. All documentation changes are isolated to README.md and TECHNICAL_DOCUMENTATION.md
2. No functional code has been modified during this documentation process
3. File creation is limited to new documentation files only
4. All changes are tracked in this documentation for audit purposes

---

*This technical documentation was generated based on systematic analysis of the codebase on [Current Date].*
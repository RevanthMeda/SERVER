# Overview

This is a comprehensive Flask-based web application for generating System Acceptance Testing (SAT) reports, specifically designed for Cully Automation. The application provides a complete user management system with role-based access control, admin approval workflows, and multi-step report generation capabilities. Users can create detailed SAT reports through a guided interface, with built-in approval workflows for Technical Managers and Project Managers, and automated document generation in Word and PDF formats.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 templates with responsive HTML/CSS design
- **UI Framework**: Custom CSS with Font Awesome icons and Google Fonts (Inter)
- **JavaScript**: Vanilla JavaScript for form interactions, signature pad integration, and CSRF token management
- **Responsive Design**: Mobile-first approach with adaptive layouts for different screen sizes

## Backend Architecture
- **Web Framework**: Flask 2.2.3 with modular blueprint structure
- **Authentication**: Flask-Login with password hashing using Werkzeug
- **Security**: CSRF protection via Flask-WTF, role-based access control decorators
- **Database ORM**: SQLAlchemy for database operations and migrations
- **Session Management**: Server-side sessions with configurable timeouts

## Database Design
- **User Management**: Users table with roles (Admin, Engineer, TM, PM), status tracking, and password hashing
- **Report Storage**: Reports table with JSON data storage for form submissions
- **System Settings**: Key-value configuration storage for application settings
- **Notifications**: User notification system with read/unread status tracking

## Document Generation
- **Template Processing**: DocxTemplate for Word document generation from templates
- **PDF Conversion**: Windows COM integration (pywin32) for automated Word-to-PDF conversion
- **File Management**: Organized directory structure for uploads, signatures, and generated outputs

## Email Integration
- **SMTP Configuration**: Gmail integration with app password authentication
- **Notification System**: Automated email notifications for approval workflows
- **Retry Logic**: Built-in retry mechanisms for email delivery failures

## Role-Based Workflow
- **Engineer Role**: Create and edit reports until Technical Manager approval
- **Technical Manager Role**: Review and approve engineer submissions
- **Project Manager Role**: Final approval and client document preparation
- **Admin Role**: Complete system oversight, user management, and configuration

## Security Features
- **Password Security**: Werkzeug password hashing with salt
- **CSRF Protection**: Token-based protection for all form submissions
- **Session Security**: HTTP-only cookies with configurable expiration
- **Input Validation**: Server-side validation for all user inputs

# Production Deployment Configuration

## Server Configuration
- **Target Server**: 172.16.18.21 (Windows Server)
- **Domain**: automation-reports.mobilehmi.org
- **Port**: 80 (production) / 5000 (development)
- **Security**: Domain-only access with IP blocking enabled

## Deployment Files
- **deploy.py**: Main production deployment script with environment setup
- **start_production.bat**: Windows batch file for easy server startup
- **middleware.py**: Security middleware for domain enforcement and IP blocking
- **DEPLOYMENT_INSTRUCTIONS.txt**: Complete deployment guide with troubleshooting

## Security Features
- **Domain-only Access**: Only allows access via automation-reports.mobilehmi.org
- **IP Blocking**: Blocks direct access via 172.16.18.21 (returns 403 Forbidden)
- **CSRF Protection**: Enhanced token-based protection for all forms
- **Security Headers**: Production-grade HTTP security headers
- **Session Security**: Secure session management with timeout controls

## External Dependencies

## Database
- **PostgreSQL**: Primary production database (configurable via DATABASE_URL)
- **SQLite**: Development fallback database with file-based storage
- **psycopg2-binary**: PostgreSQL adapter for Python

## Email Services
- **Gmail SMTP**: Email delivery through Gmail's SMTP servers
- **App Passwords**: Secure authentication using Gmail app-specific passwords

## Document Processing
- **Microsoft Word**: Required for PDF conversion functionality (Windows only)
- **pywin32**: Windows COM interface for Word automation
- **python-docx**: Word document manipulation and template processing
- **docxtpl**: Advanced template processing with variable substitution

## Web Dependencies
- **Flask Extensions**: flask-login, flask-wtf, flask-sqlalchemy for core functionality
- **Image Processing**: Pillow for image manipulation and signature processing
- **Web Scraping**: requests and beautifulsoup4 for external data integration
- **Security**: itsdangerous for secure token generation
- **Production Server**: Gunicorn for production WSGI deployment

## Frontend Libraries
- **Font Awesome 6.0**: Icon library for UI elements
- **Google Fonts**: Inter font family for consistent typography
- **Signature Pad**: signature_pad library for digital signature capture

## Development Tools
- **python-dotenv**: Environment variable management
- **logging**: Comprehensive application logging and error tracking
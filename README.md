# SAT Report Generator - Complete End-to-End Documentation

## Overview

The **SAT Report Generator** is a comprehensive Flask-based web application designed specifically for **Cully Automation** to automate the creation, approval, and management of System Acceptance Testing (SAT) reports. This application transforms a manual, time-consuming process into a streamlined digital workflow with role-based access control, automated document generation, and seamless approval workflows.

## 🎯 What This Application Does

### Core Purpose
The application automates the complete lifecycle of SAT (System Acceptance Testing) reports from creation to final client delivery:

1. **Digital Form Interface** - Replace manual Word document editing with a guided web form
2. **Automated Document Generation** - Generate professional Word documents using company templates
3. **Role-Based Approval Workflow** - Route reports through Technical Manager and Project Manager approvals
4. **User Management System** - Complete authentication, authorization, and user lifecycle management
5. **Secure Document Storage** - Organize and store all reports with proper access controls
6. **Email Notifications** - Automated notifications for approvals, rejections, and status changes

### Key Business Problems Solved
- **Manual Document Creation** → Automated template-based generation
- **Email-Based Approvals** → Integrated workflow management  
- **Document Version Control** → Centralized storage and tracking
- **Access Control Issues** → Role-based security system
- **Report Status Confusion** → Real-time status tracking
- **Client Delivery Delays** → Streamlined final document preparation

## 🏗 Complete Application Architecture

### User Roles & Responsibilities

#### **Admin**
- **User Management**: Approve new registrations, assign roles, enable/disable accounts
- **System Configuration**: Manage company logo, storage settings, system parameters
- **Database Monitoring**: Monitor system health and connectivity
- **Full Access**: Can view, edit, and manage all reports and users

#### **Engineer**
- **Report Creation**: Fill out SAT forms with technical details, test results, and supporting documentation
- **Document Upload**: Add supporting files, images, and technical drawings
- **Initial Submission**: Submit reports for Technical Manager review
- **Edit Until Approved**: Can modify reports until Technical Manager approval

#### **Technical Manager (Automation Manager)**
- **Technical Review**: Review engineering submissions for technical accuracy
- **Approve/Reject Reports**: First-stage approval with detailed feedback
- **Technical Oversight**: Ensure compliance with technical standards
- **Progress Tracking**: Monitor team's report submissions

#### **Project Manager**
- **Final Review**: Second-stage approval for client-ready documents
- **Business Validation**: Ensure reports meet project requirements
- **Client Communication**: Prepare final documents for client delivery
- **Project Oversight**: Track all project-related SAT reports

### Technical Architecture

#### **Frontend Layer**
- **Responsive Web Interface**: Mobile-friendly design using custom CSS
- **Interactive Forms**: Dynamic form fields with client-side validation
- **File Upload Handling**: Drag-and-drop file uploads with progress indicators
- **Digital Signatures**: Canvas-based signature capture for approvals
- **Real-time Updates**: AJAX-based status updates and notifications

#### **Backend Layer**
- **Flask Web Framework**: Python-based web application with modular blueprint structure
- **SQLAlchemy ORM**: Database abstraction with PostgreSQL/SQLite support
- **Authentication System**: Flask-Login with secure password hashing
- **Authorization Layer**: Role-based access control decorators
- **Email Integration**: SMTP integration for automated notifications

#### **Document Processing Engine**
- **Template Processing**: Uses company-specific Word templates (SAT_Template.docx)
- **Field Replacement**: Advanced template tag replacement system
- **Format Preservation**: Maintains company branding, colors, fonts, and styling
- **PDF Conversion**: Windows COM integration for automatic PDF generation
- **File Management**: Organized storage with proper naming conventions

#### **Database Schema**
- **Users Table**: User accounts with roles, status, and authentication data
- **Reports Table**: Complete report data with JSON storage for flexibility
- **SAT Reports Table**: Specialized SAT report structure with detailed form data
- **System Settings**: Configurable application parameters
- **Approval Tracking**: Complete audit trail of all approval actions

## 🔄 Complete User Journey

### 1. New User Onboarding
```
Visit Application → Registration Form → Admin Notification → 
Admin Approval → Role Assignment → User Activated → Dashboard Access
```

**Details:**
- Users register with full name, email, and requested role
- Registration creates "Pending" status account
- Admin receives notification and reviews request
- Admin approves and assigns appropriate role (Engineer/TM/PM)
- User receives activation notification and can log in
- User is directed to role-specific dashboard

### 2. SAT Report Creation Workflow

#### **Engineer Phase**
```
Create New Report → Fill SAT Form → Upload Files → Add Signatures → 
Submit for Review → Technical Manager Notification
```

**SAT Form Sections:**
- **Project Information**: Project reference, document title, client details, revision info
- **Personnel**: Prepared by, reviewed by (Technical Manager), approved by (Project Manager)
- **Test Results**: Detailed test data, pass/fail status, technical specifications
- **Supporting Documents**: File uploads, technical drawings, test certificates
- **Comments & Notes**: Additional technical information, special requirements
- **Digital Signatures**: Engineer signature with timestamp

#### **Technical Manager Review**
```
Receive Notification → Review Technical Content → Check Test Data → 
Add Comments → Approve/Reject → Engineer Notification
```

**Review Process:**
- Access assigned reports from TM dashboard
- Review all technical content and test results
- Verify supporting documentation completeness
- Add technical comments and feedback
- Digital signature approval for technical accuracy
- Automatic notification to Engineer (if rejected) or Project Manager (if approved)

#### **Project Manager Final Approval**
```
Receive Notification → Business Review → Client Requirements Check → 
Final Comments → Approve for Client → Document Generation
```

**Final Review Process:**
- Verify project requirements compliance
- Review client deliverable requirements
- Check document completeness and professional presentation
- Add final project comments
- Digital signature for client delivery approval
- Trigger final document generation

### 3. Document Generation Process
```
PM Approval → Template Processing → Field Replacement → 
Format Verification → PDF Generation → Storage → Download Ready
```

**Technical Process:**
- Load company SAT_Template.docx template
- Replace all template tags with actual form data:
  - `{{ PROJECT_REFERENCE }}` → Actual project number
  - `{{ DOCUMENT_TITLE }}` → Report title
  - `{{ DATE }}` → Report date
  - `{{ CLIENT_NAME }}` → Client company name
  - `{{ REVISION }}` → Document revision number
  - Plus all other form fields
- Preserve all company branding, colors, fonts, logos
- Generate both .docx and .pdf versions
- Store with standardized naming: `SAT_[PROJECT_NUMBER].docx`

### 4. Status Tracking & Notifications

#### **Report Status States**
- **DRAFT** - Being created by Engineer
- **SUBMITTED** - Awaiting Technical Manager review
- **TM_APPROVED** - Technical Manager approved, awaiting PM review
- **PM_APPROVED** - Project Manager approved, ready for client
- **REJECTED** - Rejected at any stage with feedback
- **DELIVERED** - Final document delivered to client

#### **Automated Notifications**
- **Submission Notifications** - TM notified when Engineer submits
- **Approval Notifications** - PM notified when TM approves
- **Rejection Notifications** - Engineer notified with detailed feedback
- **Final Approval** - All stakeholders notified when ready for client
- **System Alerts** - Database issues, login attempts, system status

## 🛠 Installation & Configuration

### Prerequisites
- **Python 3.7+** with pip package manager
- **PostgreSQL Database** (production) or SQLite (development)
- **Windows Server** (required for Word to PDF conversion)
- **SMTP Email Account** (Gmail recommended) for notifications
- **Network Access** to company domain (automation-reports.mobilehmi.org)

### Environment Configuration (.env)
```env
# Flask Application Configuration
SECRET_KEY=your-super-secret-key-here
CSRF_SECRET_KEY=your-csrf-protection-key
FLASK_DEBUG=False  # Set to True for development only

# Database Configuration
DATABASE_URL=postgresql://username:password@host:5432/database
# Development alternative: DATABASE_URL=sqlite:///sat_reports.db

# Email Configuration (Gmail App Password recommended)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-company-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
DEFAULT_SENDER=your-company-email@gmail.com

# Approval Workflow Configuration
APPROVER_1=techlead@company.com        # Technical Manager email
APPROVER_2=projectmanager@company.com  # Project Manager email

# Company Branding
COMPANY_NAME=Cully Automation
COMPANY_LOGO=static/images/company-logo.png

# Security Configuration
ALLOWED_DOMAINS=automation-reports.mobilehmi.org
BLOCK_IP_ACCESS=True  # Block direct IP access for security
SSL_CERT_PATH=ssl/mobilehmi.org2025.pfx  # HTTPS certificate
SSL_CERT_PASSWORD=your-certificate-password

# Feature Toggles
ENABLE_PDF_EXPORT=True
ENABLE_EMAIL_NOTIFICATIONS=True
ENABLE_HTTPS=True  # Set to False for development only
```

### Installation Steps
```bash
# 1. Clone the repository
git clone <your-repository-url>
cd sat-report-generator

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env file with your specific configuration

# 4. Initialize database
python init_new_db.py

# 5. Create admin user (first time only)
python app.py --create-admin

# 6. For production deployment
python start_production.py
# Or use the Windows batch file
start_production.bat
```

## 🚀 Production Deployment

### Server Requirements
- **Target Server**: 172.16.18.21 (Windows Server)
- **Internal Network Access**: http://172.16.18.21:5000
- **HTTPS Support**: SSL certificate (mobilehmi.org2025.pfx)
- **Security Model**: Internal company network only, no external exposure
- **Database**: PostgreSQL for production reliability

### Deployment Configuration
```python
# Production configuration in config.py
class ProductionConfig:
    DEBUG = False
    TESTING = False
    DATABASE_URL = os.getenv('DATABASE_URL')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Work day session
```

### Security Features
- **HTTPS Enforced**: All communications encrypted
- **CSRF Protection**: All forms protected against cross-site attacks
- **Password Hashing**: Werkzeug secure password hashing with salt
- **Session Security**: HTTP-only cookies with configurable expiration
- **Network Isolation**: Internal company network access only
- **Input Validation**: Server-side validation for all user inputs
- **File Upload Security**: Type and size restrictions on uploaded files

## 📊 Database Structure & Data Flow

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30),  -- Admin, Engineer, Automation Manager, PM
    status VARCHAR(20) DEFAULT 'Pending',  -- Pending, Active, Disabled
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    requested_role VARCHAR(20)
);
```

#### Reports Table (Main report storage)
```sql
CREATE TABLE reports (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    type VARCHAR(20) NOT NULL,   -- 'SAT', 'FDS', 'HDS', etc.
    status VARCHAR(20) DEFAULT 'DRAFT',
    document_title VARCHAR(200),
    document_reference VARCHAR(100),
    project_reference VARCHAR(100),
    client_name VARCHAR(200),
    user_email VARCHAR(120),
    submission_date DATETIME,
    approval_date DATETIME,
    approvals_json TEXT,  -- JSON storage of approval workflow
    data_json TEXT        -- Complete form data in JSON format
);
```

#### SAT Reports Table (Specialized SAT data)
```sql
CREATE TABLE sat_reports (
    id INTEGER PRIMARY KEY,
    report_id VARCHAR(36),  -- Foreign key to reports table
    project_reference VARCHAR(100),
    document_title VARCHAR(200),
    document_reference VARCHAR(100),
    revision VARCHAR(10),
    date_created DATE,
    client_name VARCHAR(200),
    prepared_by VARCHAR(100),
    reviewed_by_tech_lead VARCHAR(100),
    reviewed_by_pm VARCHAR(100),
    data_json TEXT,  -- Detailed SAT form data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Data Flow Architecture
```
User Input → Form Validation → Database Storage → 
Approval Workflow → Template Processing → Document Generation → 
File Storage → Download Delivery
```

## 🔧 Advanced Features

### Template Processing Engine
The application uses an advanced template processing system that:

- **Preserves Formatting**: Maintains all company branding, colors, fonts, and styling
- **Dynamic Field Replacement**: Replaces template tags with actual data
- **Invisible Tag Detection**: Handles template tags that are invisible on servers without Office
- **Automatic Tag Addition**: Adds missing template tags for server compatibility
- **Efficient Processing**: Optimized for performance to prevent application freezing

### Template Tags Supported
```
{{ PROJECT_REFERENCE }}      → Project number/code
{{ DOCUMENT_TITLE }}         → Report title
{{ DOCUMENT_REFERENCE }}     → Document reference number
{{ REVISION }}               → Document revision (R0, R1, etc.)
{{ DATE }}                   → Report creation date
{{ CLIENT_NAME }}            → Client company name
{{ PREPARED_BY }}            → Engineer name
{{ REVIEWED_BY_TECH_LEAD }}  → Technical Manager name
{{ REVIEWED_BY_PM }}         → Project Manager name
Plus all custom form fields from the SAT form
```

### File Management System
- **Organized Storage**: Separate directories for uploads, signatures, outputs
- **Naming Conventions**: Standardized file naming (SAT_PROJECTNUMBER.docx)
- **Version Control**: Automatic versioning for document revisions
- **Security**: Access-controlled file downloads based on user roles
- **Cleanup**: Automatic cleanup of temporary files and old versions

### Email Notification System
- **Template-Based Emails**: Professional HTML email templates
- **Role-Specific Content**: Different email content for different recipients
- **Retry Logic**: Built-in retry mechanism for failed email deliveries
- **Status Updates**: Real-time email notifications for all workflow changes

## 🔍 Troubleshooting & Maintenance

### Common Issues & Solutions

#### **Application Freezing**
- **Cause**: Excessive logging or inefficient document processing
- **Solution**: Optimized document processing with reduced logging
- **Prevention**: Regular performance monitoring and code optimization

#### **Template Tag Issues**
- **Cause**: Server without Microsoft Office cannot see certain template tags
- **Solution**: Automatic invisible tag detection and addition system
- **Prevention**: Use template validation before deployment

#### **Database Connection Issues**
- **Symptoms**: Red database status indicator on admin dashboard
- **Solution**: Check DATABASE_URL configuration and PostgreSQL service
- **Monitoring**: Real-time database status monitoring

#### **Email Delivery Problems**
- **Cause**: SMTP configuration or Gmail app password issues
- **Solution**: Verify SMTP settings and use Gmail app-specific passwords
- **Testing**: Built-in email testing functionality

### Maintenance Tasks

#### **Regular Maintenance**
- Monitor database performance and storage usage
- Review user account status and clean up inactive accounts
- Archive old reports and maintain storage space
- Update SSL certificates before expiration
- Review system logs for errors and performance issues

#### **Database Maintenance**
```sql
-- Clean up old session data
DELETE FROM sessions WHERE expires < NOW();

-- Archive old reports (older than 2 years)
UPDATE reports SET archived = TRUE WHERE submission_date < NOW() - INTERVAL '2 years';

-- User activity report
SELECT role, status, COUNT(*) FROM users GROUP BY role, status;
```

## 📞 Support & Contact Information

### For System Administrators
- **Application Issues**: Check application logs in `/logs/application.log`
- **Database Issues**: Monitor PostgreSQL logs and connection status
- **Email Issues**: Verify SMTP configuration and Gmail app passwords
- **SSL Certificate**: Monitor certificate expiration dates

### For End Users
- **Login Issues**: Contact system administrator for account status
- **Report Problems**: Check report status page for detailed workflow information
- **File Upload Issues**: Verify file types and sizes meet requirements
- **Approval Delays**: Contact appropriate Technical Manager or Project Manager

### Technical Support
- **Development Team**: Cully Automation Technical Team
- **System Monitoring**: Admin dashboard provides real-time system status
- **Documentation**: This comprehensive README file
- **Issue Reporting**: Use company internal support channels

---

## 🎯 Business Value & ROI

### Efficiency Improvements
- **Report Creation Time**: Reduced from 2-3 hours to 30 minutes
- **Approval Workflow**: Automated routing saves 1-2 days per report
- **Document Consistency**: 100% compliance with company templates
- **Error Reduction**: Eliminated manual document editing errors
- **Status Tracking**: Real-time visibility into all report progress

### Operational Benefits
- **Centralized Storage**: All reports in one secure, accessible location
- **Audit Trail**: Complete history of all changes and approvals
- **Role-Based Security**: Proper access controls and user management
- **Professional Output**: Consistently branded, professional client documents
- **Scalability**: System can handle unlimited users and reports

### Cost Savings
- **Reduced Manual Labor**: Automation eliminates repetitive manual tasks
- **Faster Client Delivery**: Streamlined process improves project timelines
- **Reduced Errors**: Automated validation prevents costly mistakes
- **Better Resource Utilization**: Engineers and managers focus on value-add activities

This SAT Report Generator represents a complete digital transformation of Cully Automation's report management process, providing a modern, efficient, and secure solution for all SAT report needs.

---

**Version**: Production Ready  
**Last Updated**: 2025  
**Deployment Target**: 172.16.18.21:5000 (Internal Network)  
**Security Level**: Company Confidential - Internal Use Only
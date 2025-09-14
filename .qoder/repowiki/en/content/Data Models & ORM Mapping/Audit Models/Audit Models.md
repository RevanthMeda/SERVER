# Audit Models

<cite>
**Referenced Files in This Document**   
- [models.py](file://models.py)
- [routes/compare.py](file://routes/compare.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [ReportVersion Model](#reportversion-model)
3. [ReportEdit Model](#reportedits-model)
4. [Notification Model](#notification-model)
5. [ReportComment Model](#reportcomment-model)
6. [UserAnalytics Model](#useranalytics-model)
7. [Webhook Model](#webhook-model)
8. [SavedSearch Model](#savedsearch-model)
9. [Data Retention and Performance](#data-retention-and-performance)
10. [Examples and Usage](#examples-and-usage)

## Introduction
This document provides comprehensive documentation for the audit and versioning models in the SAT Report Generator application. The models covered include ReportVersion, ReportEdit, Notification, ReportComment, UserAnalytics, Webhook, and SavedSearch. These models support document version control, audit trails, user notifications, collaboration features, performance tracking, and system integrations. The documentation details field definitions, relationships, and usage patterns for each model, along with performance considerations for high-volume audit logging and time-series queries.

## ReportVersion Model

The ReportVersion model implements document version control by tracking changes to reports over time. Each version record captures a snapshot of the report state at a specific point in time, enabling historical tracking and rollback capabilities.

### Key Fields
- **version_number**: String identifier for the version (e.g., "R0", "R1", "R2")
- **created_at**: Timestamp when the version was created (UTC)
- **created_by**: Email of the user who created the version
- **change_summary**: Text description of changes made in this version
- **data_snapshot**: JSON string containing the complete state of the report data
- **file_path**: Optional path to the generated document file
- **is_current**: Boolean flag indicating if this is the current active version

### Data Snapshot Implementation
The data_snapshot field preserves the complete JSON state of the report for historical tracking. When a new version is created, the system captures the current report data as a JSON string, ensuring that all field values are preserved exactly as they existed at that moment. This approach enables accurate comparison between versions and supports the application's version diff functionality.

### Version Management
The model maintains the invariant that only one version per report can have is_current=True. When a new version is created, the system automatically updates all existing versions for that report to set is_current=False, ensuring data consistency.

**Section sources**
- [models.py](file://models.py#L238-L253)
- [routes/compare.py](file://routes/compare.py#L97-L134)

## ReportEdit Model

The ReportEdit model serves as an audit trail for tracking changes made to reports. It captures both the before and after states of report data, along with metadata about the edit operation.

### Key Fields
- **report_id**: Foreign key to the report being edited
- **editor_user_id**: Foreign key to the User who made the edit
- **editor_email**: Email address of the editor (stored for reference)
- **before_json**: JSON string representing the report state before the edit
- **after_json**: JSON string representing the report state after the edit
- **changes_summary**: Human-readable summary of the changes made
- **created_at**: Timestamp when the edit was made (UTC)
- **version_before**: Version number before the edit (e.g., "R0")
- **version_after**: Version number after the edit (e.g., "R1")

### Audit Trail Functionality
The model provides a complete record of all modifications to reports, enabling forensic analysis of changes. By storing both before and after states as JSON, the system can reconstruct the exact data transformation that occurred during each edit. The changes_summary field provides context for the changes, while the version transition fields link edits to the versioning system.

### Relationships
The model establishes relationships with both the Report and User models through foreign keys, enabling efficient querying of edit history by report or by user.

**Section sources**
- [models.py](file://models.py#L623-L643)

## Notification Model

The Notification model manages in-app alerts and notifications for users, supporting various notification types and action workflows.

### Key Fields
- **user_email**: Recipient's email address
- **title**: Notification title (200 character limit)
- **message**: Notification content (text field)
- **type**: Discriminator for notification type (e.g., "approval_request", "status_update", "completion")
- **related_submission_id**: Optional link to a report submission
- **read**: Boolean flag indicating if the notification has been read
- **created_at**: Timestamp when the notification was created (UTC)
- **action_url**: Optional URL for taking action on the notification

### Notification Types
The type field supports discrimination between different notification categories:
- **approval_request**: Notifications for pending report approvals
- **status_update**: Updates on report status changes
- **completion**: Notifications when reports are completed
- Other types as needed for system events

### Read State Management
The read field enables tracking of notification status, allowing the system to display unread counts and highlight new notifications in the user interface.

**Section sources**
- [models.py](file://models.py#L645-L700)

## ReportComment Model

The ReportComment model implements a hierarchical comment system for collaboration on reports, supporting threaded discussions and user mentions.

### Key Fields
- **report_id**: Foreign key to the report being commented on
- **user_email**: Email of the commenting user
- **user_name**: Name of the commenting user
- **comment_text**: The comment content (text field)
- **field_reference**: Optional reference to a specific field/section
- **created_at**: Timestamp when the comment was created (UTC)
- **updated_at**: Timestamp when the comment was last updated (UTC)
- **is_resolved**: Boolean flag indicating if the comment has been resolved
- **resolved_by**: Email of the user who resolved the comment
- **resolved_at**: Timestamp when the comment was resolved
- **parent_comment_id**: Self-referential foreign key for threading
- **mentions_json**: JSON array of mentioned users

### Hierarchical Comment System
The model supports threaded conversations through the parent_comment_id field, which references another comment in the same table. This self-referential relationship enables nested replies and discussion threads. The replies relationship provides bidirectional navigation through the comment hierarchy.

### Collaboration Features
The mentions_json field stores an array of mentioned users as JSON, enabling @-mention functionality similar to social media platforms. This feature facilitates targeted collaboration and notifications to specific team members.

**Section sources**
- [models.py](file://models.py#L255-L277)

## UserAnalytics Model

The UserAnalytics model tracks performance metrics and KPIs for users, enabling measurement of productivity and efficiency.

### Key Fields
- **user_email**: Email of the tracked user
- **date**: Date of the metrics (date field)
- **reports_created**: Count of reports created by the user
- **reports_approved**: Count of reports approved by the user
- **reports_rejected**: Count of reports rejected by the user
- **avg_completion_time**: Average time to complete reports (hours)
- **approval_cycle_time**: Average time for approval cycle (hours)
- **on_time_percentage**: Percentage of reports completed on time
- **custom_metrics**: JSON field for additional custom metrics

### Performance Tracking
The model aggregates key performance indicators at the daily level, enabling trend analysis over time. The KPIs include:
- **reports_created**: Measures user productivity in generating reports
- **reports_approved**: Tracks approval throughput for managers
- **avg_completion_time**: Measures efficiency in completing reports
- **approval_cycle_time**: Measures the duration of the approval process

### Custom Metrics
The custom_metrics field provides extensibility for additional metrics not covered by the standard fields, stored as JSON to accommodate varying data structures.

**Section sources**
- [models.py](file://models.py#L218-L236)

## Webhook Model

The Webhook model supports event-driven integrations by storing webhook configurations for workflow automation.

### Key Fields
- **name**: Descriptive name for the webhook
- **url**: Target URL for the webhook POST request
- **event_type**: Event that triggers the webhook (e.g., "submission", "approval", "rejection", "completion")
- **is_active**: Boolean flag indicating if the webhook is enabled
- **headers_json**: JSON object containing custom headers for the request
- **created_by**: Email of the user who created the webhook
- **created_at**: Timestamp when the webhook was created (UTC)
- **last_triggered**: Timestamp of the last successful trigger
- **trigger_count**: Counter for the number of times the webhook has been triggered

### Integration Capabilities
The model enables integration with external systems by allowing configuration of HTTP callbacks for specific events. The headers_json field supports custom authentication and content-type headers, while the event_type field provides discrimination between different trigger conditions.

**Section sources**
- [models.py](file://models.py#L279-L295)

## SavedSearch Model

The SavedSearch model stores user-defined search filters for quick access to frequently used queries.

### Key Fields
- **name**: Descriptive name for the saved search
- **user_email**: Owner of the saved search
- **filters_json**: JSON representation of the search criteria
- **is_public**: Boolean flag indicating if the search is shared with the team
- **created_at**: Timestamp when the search was created (UTC)
- **last_used**: Timestamp of the last use
- **use_count**: Counter for the number of times the search has been used

### Productivity Enhancement
The model improves user productivity by allowing storage and reuse of complex search criteria. The filters_json field captures the complete search configuration as JSON, enabling restoration of the exact search state. Public searches (is_public=True) can be shared across teams, promoting consistency in reporting and analysis.

**Section sources**
- [models.py](file://models.py#L297-L311)

## Data Retention and Performance

### Data Retention Policies
The system implements data retention policies through the ReportArchive model, which archives old reports based on configurable retention periods. The retention_until field specifies when archived data can be permanently deleted, ensuring compliance with data governance requirements.

### Indexing Strategies
For time-series queries, the system employs indexing strategies on timestamp fields:
- **created_at** fields are indexed for efficient chronological queries
- **date** fields in analytics tables are indexed for daily aggregations
- Composite indexes are used for queries filtering by user and date

### Performance Implications
High-volume audit logging presents performance considerations:
- **Storage**: Audit records can grow rapidly, requiring appropriate storage planning
- **Query Performance**: Large audit trails may impact query performance, mitigated by proper indexing
- **Archiving**: Regular archiving of old audit records maintains system performance
- **Purging**: Configurable retention policies enable automatic cleanup of obsolete audit data

**Section sources**
- [models.py](file://models.py#L218-L311)

## Examples and Usage

### Audit Log Generation
When a report is edited, the system creates a ReportEdit record:
```python
edit = ReportEdit(
    report_id=report.id,
    editor_user_id=current_user.id,
    editor_email=current_user.email,
    before_json=json.dumps(old_data),
    after_json=json.dumps(new_data),
    changes_summary="Updated client information and project scope",
    version_before="R0",
    version_after="R1"
)
db.session.add(edit)
db.session.commit()
```

### Notification Creation
Creating a notification for a user:
```python
Notification.create_notification(
    user_email="engineer@company.com",
    title="Approval Request",
    message="Your report requires approval",
    notification_type="approval_request",
    submission_id="abc123",
    action_url="/reports/abc123/approve"
)
```

### Analytics Aggregation
Aggregating daily user analytics:
```python
analytics = UserAnalytics(
    user_email=user.email,
    date=datetime.utcnow().date(),
    reports_created=5,
    reports_approved=3,
    avg_completion_time=2.5,
    approval_cycle_time=1.8
)
db.session.add(analytics)
db.session.commit()
```

**Section sources**
- [models.py](file://models.py#L218-L700)
- [routes/compare.py](file://routes/compare.py#L97-L134)
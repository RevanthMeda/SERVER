# Collaboration & Edit Tracking

<cite>
**Referenced Files in This Document**   
- [models.py](file://models.py#L238-L277)
- [routes/collaboration.py](file://routes/collaboration.py#L0-L292)
- [routes/compare.py](file://routes/compare.py#L0-L134)
- [api/versioning.py](file://api/versioning.py#L0-L273)
- [templates/pending_approval.html](file://templates/pending_approval.html#L32-L82)
- [routes/edit.py](file://routes/edit.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Collaboration Features](#collaboration-features)
3. [Edit Tracking Implementation](#edit-tracking-implementation)
4. [Version History System](#version-history-system)
5. [UI Integration](#ui-integration)
6. [API Endpoints for Version Comparison](#api-endpoints-for-version-comparison)
7. [Data Consistency and Concurrency](#data-consistency-and-concurrency)
8. [Comment Moderation and Retention](#comment-moderation-and-retention)
9. [Performance Optimization](#performance-optimization)
10. [Conclusion](#conclusion)

## Introduction
This document details the collaboration, edit tracking, and version history features of the SAT Report Generator application. The system enables multiple users to collaborate on reports through comments, tracks all changes made during editing, and maintains a comprehensive version history. These features support review cycles, ensure data integrity, and provide audit trails for compliance purposes.

## Collaboration Features

The collaboration system allows users to add comments during review cycles using dedicated endpoints. Users can comment on specific fields, mention colleagues, and track comment resolution status.

```mermaid
sequenceDiagram
participant User as "User"
participant Frontend as "Frontend"
participant Backend as "Backend"
participant Database as "Database"
User->>Frontend : Add comment with @mention
Frontend->>Backend : POST /api/add-comment
Backend->>Database : Store comment
Backend->>Backend : Extract mentions
Backend->>Backend : Send notifications
Backend-->>Frontend : Return success
Frontend-->>User : Show confirmation
Backend->>User : Send notification (if mentioned)
```

**Diagram sources**
- [routes/collaboration.py](file://routes/collaboration.py#L72-L103)
- [models.py](file://models.py#L255-L277)

**Section sources**
- [routes/collaboration.py](file://routes/collaboration.py#L0-L292)
- [models.py](file://models.py#L255-L277)

## Edit Tracking Implementation

The system implements comprehensive edit tracking that captures changes to report fields before submission. All modifications are recorded with timestamps, user information, and field references.

```mermaid
classDiagram
class ReportComment {
+int id
+string report_id
+string user_email
+string user_name
+string comment_text
+string field_reference
+datetime created_at
+datetime updated_at
+bool is_resolved
+string resolved_by
+datetime resolved_at
+int parent_comment_id
+string mentions_json
}
ReportComment --> ReportComment : "replies"
```

**Diagram sources**
- [models.py](file://models.py#L255-L277)
- [routes/collaboration.py](file://routes/collaboration.py#L72-L103)

**Section sources**
- [models.py](file://models.py#L255-L277)
- [routes/collaboration.py](file://routes/collaboration.py#L72-L103)

## Version History System

The versioning system creates snapshots using the `ReportVersion` model upon major state transitions. Each version captures the complete state of the report at that point in time.

```mermaid
classDiagram
class ReportVersion {
+int id
+string report_id
+string version_number
+datetime created_at
+string created_by
+string change_summary
+string data_snapshot
+string file_path
+bool is_current
}
```

**Diagram sources**
- [models.py](file://models.py#L238-L253)
- [routes/compare.py](file://routes/compare.py#L97-L134)

**Section sources**
- [models.py](file://models.py#L238-L253)
- [routes/compare.py](file://routes/compare.py#L97-L134)

## UI Integration

The UI integrates with `pending_approval.html` and `edit.py` routes to highlight changes and facilitate collaboration. The pending approval page displays the current status of reports awaiting review.

```mermaid
flowchart TD
Start([User opens report]) --> CheckStatus["Check report status"]
CheckStatus --> IsPending{"Status = Pending?"}
IsPending --> |Yes| ShowPending["Render pending_approval.html"]
IsPending --> |No| ShowEditor["Render edit interface"]
ShowPending --> Highlight["Highlight pending items"]
Highlight --> EnableComments["Enable comment functionality"]
EnableComments --> End([User can comment/approve])
```

**Diagram sources**
- [templates/pending_approval.html](file://templates/pending_approval.html#L32-L82)
- [routes/edit.py](file://routes/edit.py)

**Section sources**
- [templates/pending_approval.html](file://templates/pending_approval.html#L32-L82)
- [routes/edit.py](file://routes/edit.py)

## API Endpoints for Version Comparison

The version comparison APIs in `api/versioning.py` enable clients to retrieve and compare different versions of reports. These endpoints support both HTML and JSON responses for flexibility.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Server as "Server"
participant DB as "Database"
Client->>Server : GET /api/diff-data/{report_id}
Server->>Server : Validate parameters
Server->>DB : Query version1
Server->>DB : Query version2
DB-->>Server : Return snapshots
Server->>Server : Parse JSON data
Server->>Server : Generate field diff
Server-->>Client : Return diff results
```

**Diagram sources**
- [api/versioning.py](file://api/versioning.py#L0-L273)
- [routes/compare.py](file://routes/compare.py#L64-L100)

**Section sources**
- [api/versioning.py](file://api/versioning.py#L0-L273)
- [routes/compare.py](file://routes/compare.py#L64-L100)

## Data Consistency and Concurrency

The system addresses data consistency challenges during concurrent edits through transaction management and locking mechanisms. When multiple users edit the same report, the system ensures that changes are applied in a controlled manner.

```mermaid
flowchart TD
A([User begins edit]) --> B["Acquire record lock"]
B --> C["Load current version"]
C --> D["Make changes"]
D --> E["Validate changes"]
E --> F["Commit transaction"]
F --> G["Release lock"]
H["Concurrent edit attempt"] --> I{"Lock available?"}
I --> |No| J["Wait for lock"]
I --> |Yes| K["Proceed with edit"]
```

**Section sources**
- [routes/edit.py](file://routes/edit.py)
- [models.py](file://models.py#L238-L253)

## Comment Moderation and Retention

The comment moderation workflow includes features for resolving, reopening, and deleting comments. Only comment authors and administrators can modify or delete comments, ensuring accountability.

```mermaid
stateDiagram-v2
[*] --> Active
Active --> Resolved : resolve_comment()
Resolved --> Active : unresolve_comment()
Active --> Deleted : delete_comment()
Resolved --> Deleted : delete_comment()
note right of Resolved
Only author or admin
can resolve/unresolve
end note
note left of Deleted
Only author or admin
can delete
end note
```

**Section sources**
- [routes/collaboration.py](file://routes/collaboration.py#L103-L174)
- [models.py](file://models.py#L255-L277)

## Performance Optimization

For querying version diffs on large reports, several performance tips are recommended:
- Use selective field loading to minimize data transfer
- Implement caching for frequently accessed version pairs
- Optimize JSON parsing with streaming parsers
- Use database indexing on report_id and created_at fields
- Implement pagination for version history displays

```mermaid
flowchart LR
A["Performance Tips"] --> B["Index report_id and created_at"]
A --> C["Cache frequent version comparisons"]
A --> D["Use selective field queries"]
A --> E["Implement result pagination"]
A --> F["Optimize JSON serialization"]
```

**Section sources**
- [api/versioning.py](file://api/versioning.py#L0-L273)
- [routes/compare.py](file://routes/compare.py#L64-L100)

## Conclusion
The collaboration, edit tracking, and version history features provide a comprehensive solution for team-based report development and review. By combining comment functionality, detailed change tracking, and robust version management, the system supports efficient workflows while maintaining data integrity and auditability. The implementation balances usability with performance, ensuring that these features remain responsive even with large reports and extensive history.
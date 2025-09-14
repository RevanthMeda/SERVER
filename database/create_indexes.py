"""
Create database indexes for performance optimization
"""
from sqlalchemy import create_engine, text, Index
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def create_performance_indexes(db):
    """Create indexes for frequently queried columns"""
    
    indexes_to_create = [
        # Reports table indexes
        ('idx_reports_status', 'reports', ['status']),
        ('idx_reports_user_email', 'reports', ['user_email']),
        ('idx_reports_created_at', 'reports', ['created_at']),
        ('idx_reports_status_created', 'reports', ['status', 'created_at']),
        ('idx_reports_user_status', 'reports', ['user_email', 'status']),
        
        # Users table indexes
        ('idx_users_status', 'users', ['status']),
        ('idx_users_role', 'users', ['role']),
        ('idx_users_email', 'users', ['email']),
        ('idx_users_status_role', 'users', ['status', 'role']),
        
        # Notifications table indexes
        ('idx_notifications_user_email', 'notifications', ['user_email']),
        ('idx_notifications_read', 'notifications', ['read']),
        ('idx_notifications_user_read', 'notifications', ['user_email', 'read']),
        ('idx_notifications_created_at', 'notifications', ['created_at']),
        
        # SAT Reports table indexes
        ('idx_sat_reports_report_id', 'sat_reports', ['report_id']),
        
        # System Settings table indexes
        ('idx_system_settings_key', 'system_settings', ['key']),
    ]
    
    created_indexes = []
    existing_indexes = []
    failed_indexes = []
    
    with db.engine.connect() as conn:
        for index_name, table_name, columns in indexes_to_create:
            try:
                # Check if index already exists
                if db.engine.dialect.name == 'postgresql':
                    result = conn.execute(text(
                        "SELECT 1 FROM pg_indexes WHERE indexname = :index_name"
                    ), {'index_name': index_name})
                    exists = result.fetchone() is not None
                elif db.engine.dialect.name == 'sqlite':
                    result = conn.execute(text(
                        "SELECT 1 FROM sqlite_master WHERE type='index' AND name = :index_name"
                    ), {'index_name': index_name})
                    exists = result.fetchone() is not None
                else:
                    # For other databases, try to create and handle error if exists
                    exists = False
                
                if not exists:
                    # Create the index
                    columns_str = ', '.join(columns)
                    create_index_sql = f"CREATE INDEX {index_name} ON {table_name} ({columns_str})"
                    conn.execute(text(create_index_sql))
                    conn.commit()
                    created_indexes.append(index_name)
                    logger.info(f"Created index: {index_name}")
                else:
                    existing_indexes.append(index_name)
                    logger.debug(f"Index already exists: {index_name}")
                    
            except Exception as e:
                failed_indexes.append((index_name, str(e)))
                logger.error(f"Failed to create index {index_name}: {e}")
    
    # Log summary
    logger.info(f"Index creation summary:")
    logger.info(f"  Created: {len(created_indexes)} indexes")
    logger.info(f"  Already existing: {len(existing_indexes)} indexes")
    logger.info(f"  Failed: {len(failed_indexes)} indexes")
    
    if failed_indexes:
        logger.error("Failed indexes:")
        for index_name, error in failed_indexes:
            logger.error(f"  {index_name}: {error}")
    
    return {
        'created': created_indexes,
        'existing': existing_indexes,
        'failed': failed_indexes
    }

def drop_unused_indexes(db):
    """Drop indexes that are no longer needed"""
    
    indexes_to_drop = [
        # Add any indexes that should be removed
        # Example: ('old_index_name', 'table_name')
    ]
    
    dropped_indexes = []
    failed_drops = []
    
    with db.engine.connect() as conn:
        for index_name, table_name in indexes_to_drop:
            try:
                drop_index_sql = f"DROP INDEX IF EXISTS {index_name}"
                conn.execute(text(drop_index_sql))
                conn.commit()
                dropped_indexes.append(index_name)
                logger.info(f"Dropped index: {index_name}")
            except Exception as e:
                failed_drops.append((index_name, str(e)))
                logger.error(f"Failed to drop index {index_name}: {e}")
    
    return {
        'dropped': dropped_indexes,
        'failed': failed_drops
    }

def analyze_tables(db):
    """Run ANALYZE on tables to update statistics (PostgreSQL/SQLite)"""
    
    tables_to_analyze = [
        'reports', 'users', 'notifications', 'sat_reports', 
        'system_settings', 'audit_logs', 'api_usage'
    ]
    
    analyzed_tables = []
    failed_tables = []
    
    with db.engine.connect() as conn:
        for table_name in tables_to_analyze:
            try:
                if db.engine.dialect.name == 'postgresql':
                    conn.execute(text(f"ANALYZE {table_name}"))
                elif db.engine.dialect.name == 'sqlite':
                    conn.execute(text(f"ANALYZE {table_name}"))
                elif db.engine.dialect.name == 'mysql':
                    conn.execute(text(f"ANALYZE TABLE {table_name}"))
                
                conn.commit()
                analyzed_tables.append(table_name)
                logger.info(f"Analyzed table: {table_name}")
            except Exception as e:
                failed_tables.append((table_name, str(e)))
                logger.error(f"Failed to analyze table {table_name}: {e}")
    
    return {
        'analyzed': analyzed_tables,
        'failed': failed_tables
    }

def optimize_database(db):
    """Run all database optimizations"""
    
    logger.info("Starting database optimization...")
    
    # Create indexes
    index_results = create_performance_indexes(db)
    
    # Drop unused indexes
    drop_results = drop_unused_indexes(db)
    
    # Analyze tables
    analyze_results = analyze_tables(db)
    
    # Vacuum database (SQLite only)
    if db.engine.dialect.name == 'sqlite':
        try:
            with db.engine.connect() as conn:
                conn.execute(text("VACUUM"))
                conn.commit()
                logger.info("Database vacuumed successfully")
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
    
    logger.info("Database optimization completed")
    
    return {
        'indexes': index_results,
        'dropped_indexes': drop_results,
        'analyzed_tables': analyze_results
    }

if __name__ == '__main__':
    # This can be run as a standalone script
    from app import create_app
    from models import db
    
    app = create_app('production')
    with app.app_context():
        results = optimize_database(db)
        print("Database optimization results:")
        print(f"  Created indexes: {results['indexes']['created']}")
        print(f"  Existing indexes: {results['indexes']['existing']}")
        print(f"  Failed indexes: {results['indexes']['failed']}")
        print(f"  Analyzed tables: {results['analyzed_tables']['analyzed']}")
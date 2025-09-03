from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from auth import admin_required, role_required
from models import db, User, Report, Notification, SystemSettings, test_db_connection
from utils import get_unread_count
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def home():
    """Role-based dashboard home"""
    role = current_user.role

    if role == 'Admin':
        return redirect(url_for('dashboard.admin'))
    elif role == 'Engineer':
        return redirect(url_for('dashboard.engineer'))
    elif role == 'TM':
        return redirect(url_for('dashboard.tm'))
    elif role == 'PM':
        return redirect(url_for('dashboard.pm'))
    else:
        flash('Invalid role. Contact your administrator.', 'error')
        return redirect(url_for('auth.logout'))

@dashboard_bp.route('/admin')
@admin_required
def admin():
    """Admin dashboard"""
    from models import Report, Notification

    users = User.query.all()
    db_connected = test_db_connection()

    # Calculate user statistics
    total_users = len(users)
    active_users = len([u for u in users if u.status == 'Active'])
    pending_users_count = len([u for u in users if u.status == 'Pending'])

    # Get unread notifications count
    try:
        unread_count = Notification.query.filter_by(
            user_email=current_user.email,
            read=False
        ).count()
    except Exception as e:
        current_app.logger.warning(f"Could not get unread count for admin: {e}")
        unread_count = 0

    # Get recent users (last 5)
    recent_users = User.query.order_by(User.created_date.desc()).limit(5).all()

    # Get actual pending users (users who need approval)
    pending_users_list = User.query.filter_by(status='Pending').order_by(User.created_date.desc()).limit(5).all()

    # Calculate report statistics
    try:
        total_reports = Report.query.count()
        current_app.logger.info(f"Admin dashboard: Found {total_reports} total reports")
        
        recent_reports = Report.query.order_by(Report.created_at.desc()).limit(5).all()
        current_app.logger.info(f"Admin dashboard: Processing {len(recent_reports)} recent reports")
        
        # Add basic report info for display
        for report in recent_reports:
            # Start with basic data
            report.document_title = report.document_title or 'Untitled Report'
            report.project_reference = report.project_reference or 'N/A'
            report.status = 'draft'
            
            # Try to get enhanced data from SAT report
            try:
                sat_report = SATReport.query.filter_by(report_id=report.id).first()
                if sat_report and sat_report.data_json:
                    data = json.loads(sat_report.data_json)
                    context_data = data.get('context', {})
                    if context_data.get('DOCUMENT_TITLE'):
                        report.document_title = context_data['DOCUMENT_TITLE']
                    if context_data.get('PROJECT_REFERENCE'):
                        report.project_reference = context_data['PROJECT_REFERENCE']
            except Exception as sat_error:
                current_app.logger.debug(f"Could not get SAT data for report {report.id}: {sat_error}")

            # Determine status from approvals
            if report.approvals_json:
                try:
                    approvals = json.loads(report.approvals_json)
                    if approvals:
                        statuses = [a.get("status", "pending") for a in approvals]
                        if "rejected" in statuses:
                            report.status = "rejected"
                        elif all(status == "approved" for status in statuses):
                            report.status = "approved"
                        elif any(status == "approved" for status in statuses):
                            report.status = "partially_approved"
                        else:
                            report.status = "pending"
                except Exception as approval_error:
                    current_app.logger.debug(f"Could not parse approvals for report {report.id}: {approval_error}")
                    report.status = "pending"
                    
    except Exception as e:
        current_app.logger.error(f"Could not retrieve report statistics for admin: {e}", exc_info=True)
        total_reports = 0
        recent_reports = []

    # System status
    system_status = "Online" if db_connected else "Offline"

    # Get settings
    company_logo = SystemSettings.get_setting('company_logo', 'static/cully.png')
    storage_location = SystemSettings.get_setting('default_storage_location', '/outputs/')

    return render_template('admin_dashboard.html',
                         users=users,
                         total_users=total_users,
                         pending_users=pending_users_count,
                         total_reports=total_reports,
                         db_status=db_connected,
                         recent_activity=[],  # Placeholder for recent activity
                         pending_users_list=pending_users_list,
                         storage_location=storage_location,
                         company_logo=company_logo)

@dashboard_bp.route('/engineer')
@role_required(['Engineer'])
def engineer():
    """Engineer dashboard"""
    from models import Report, Notification
    import json

    # Get unread notifications count
    try:
        unread_count = Notification.query.filter_by(
            user_email=current_user.email,
            read=False
        ).count()
    except Exception as e:
        current_app.logger.warning(f"Could not get unread count for engineer: {e}")
        unread_count = 0

    # Get report statistics for current user
    user_reports = Report.query.filter_by(user_email=current_user.email).all()

    # Calculate statistics
    total_reports = len(user_reports)
    pending_reports = 0
    approved_reports = 0

    for report in user_reports:
        if report.approvals_json:
            try:
                approvals = json.loads(report.approvals_json)
                statuses = [a.get("status", "pending") for a in approvals]

                if all(status == "approved" for status in statuses):
                    approved_reports += 1
                elif any(status == "pending" for status in statuses):
                    pending_reports += 1
            except json.JSONDecodeError:
                current_app.logger.warning(f"Could not decode approvals_json for report ID: {report.id}")
                pending_reports += 1 # Consider it pending if decoding fails
        else:
            pending_reports += 1

    stats = {
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'approved_reports': approved_reports
    }

    return render_template('engineer_dashboard.html', stats=stats, unread_count=unread_count)

@dashboard_bp.route('/tm')
@role_required(['TM'])
def tm():
    """Technical Manager dashboard"""
    from models import Report, Notification
    import json

    # Get unread notifications count
    try:
        unread_count = Notification.query.filter_by(
            user_email=current_user.email,
            read=False
        ).count()
    except Exception as e:
        current_app.logger.warning(f"Could not get unread count for TM: {e}")
        unread_count = 0

    # Get reports count for TM
    reports_count = Report.query.filter_by(status='pending_review').count()

    # Get pending approvals assigned to current TM
    # Since approvals are stored as JSON in Report.approvals_json, we need to check those
    pending_approvals = 0
    try:
        all_reports = Report.query.all()
        for report in all_reports:
            if report.approvals_json:
                try:
                    approvals = json.loads(report.approvals_json)
                    for approval in approvals:
                        if (approval.get('approver_email') == current_user.email and 
                            approval.get('status') == 'pending'):
                            pending_approvals += 1
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        current_app.logger.warning(f"Could not count pending approvals for TM: {e}")
        pending_approvals = 0

    # Get approved reports count
    approved_reports_count = Report.query.filter_by(status='approved').count()

    # Test database connection
    try:
        db_status = test_db_connection()
    except Exception as e:
        current_app.logger.warning(f"Database connection test failed: {e}")
        db_status = False

    return render_template('tm_dashboard.html',
                         unread_count=unread_count,
                         reports_count=reports_count,
                         pending_approvals=pending_approvals,
                         approved_reports_count=approved_reports_count,
                         db_status=db_status)

    # Get team reports count (reports under TM's review)
    team_reports_count = Report.query.filter_by(status='pending_review').count()

    # Get recent pending reports for display
    pending_reports = Report.query.filter_by(status='pending_review').limit(5).all()

    # Enrich pending_reports with SATReport data if available
    for report in pending_reports:
        if hasattr(report, 'sat_report') and report.sat_report:
            try:
                data = json.loads(report.sat_report.data_json)
                report.document_title = data.get('context', {}).get('DOCUMENT_TITLE', 'Untitled Report')
                report.project_reference = data.get('context', {}).get('PROJECT_REFERENCE', 'N/A')
            except Exception as e:
                current_app.logger.warning(f"Could not parse SATReport data for report {report.id}: {e}")
                report.document_title = 'Untitled Report'
                report.project_reference = 'N/A'
        else:
            report.document_title = 'Untitled Report'
            report.project_reference = 'N/A'

    return render_template('tm_dashboard.html',
                         reports_count=reports_count,
                         pending_approvals=pending_approvals,
                         approved_reports=approved_reports_count,
                         team_reports=team_reports_count,
                         recent_reports=pending_reports,
                         unread_count=unread_count)


@dashboard_bp.route('/pm')
@role_required(['PM'])
def pm():
    """Project Manager dashboard"""
    from models import Report, Notification
    import json

    # Get unread notifications count
    try:
        unread_count = Notification.query.filter_by(
            user_email=current_user.email,
            read=False
        ).count()
    except Exception as e:
        current_app.logger.warning(f"Could not get unread count for PM: {e}")
        unread_count = 0

    # Get basic statistics for PM dashboard
    try:
        # For now, show placeholder data - in future this would be filtered by projects the PM manages
        project_count = 5  # Placeholder
        pending_deliverables = 3  # Placeholder
        completed_reports = 12  # Placeholder
        on_time_percentage = 85  # Placeholder

        # Get recent reports (placeholder - would be project-specific in real implementation)
        recent_reports = []

        return render_template('pm_dashboard.html',
                             project_count=project_count,
                             pending_deliverables=pending_deliverables,
                             completed_reports=completed_reports,
                             on_time_percentage=on_time_percentage,
                             recent_reports=recent_reports,
                             unread_count=unread_count)
    except Exception as e:
        # If there's any error, provide default values
        current_app.logger.error(f"Error in PM dashboard: {e}")
        return render_template('pm_dashboard.html',
                             project_count=0,
                             pending_deliverables=0,
                             completed_reports=0,
                             on_time_percentage=0,
                             recent_reports=[],
                             unread_count=0)

# Legacy redirects for dashboard routes
@dashboard_bp.route('/technical-manager')
@role_required(['TM'])
def technical_manager():
    """Legacy redirect for TM dashboard"""
    return redirect(url_for('dashboard.tm'))

@dashboard_bp.route('/project-manager')
@role_required(['PM'])
def project_manager():
    """Legacy redirect for PM dashboard"""
    return redirect(url_for('dashboard.pm'))

@dashboard_bp.route('/user-management')
@admin_required
def user_management():
    """User management page"""
    status_filter = request.args.get('status', 'All')

    if status_filter == 'All':
        users = User.query.all()
    else:
        users = User.query.filter_by(status=status_filter).all()

    return render_template('user_management.html', users=users, current_filter=status_filter)

@dashboard_bp.route('/approve-user/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    """Approve a user and assign role"""
    user = User.query.get_or_404(user_id)
    role = request.form.get('role')

    if role not in ['Admin', 'Engineer', 'Automation Manager', 'PM']:
        flash('Invalid role selection.', 'error')
        return redirect(url_for('dashboard.user_management'))

    user.role = role
    user.status = 'Active'

    try:
        db.session.commit()
        flash(f'User {user.full_name} approved as {role}.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to approve user {user.full_name} ({user_id}): {e}")
        flash('Failed to approve user.', 'error')

    return redirect(url_for('dashboard.user_management'))

@dashboard_bp.route('/disable-user/<int:user_id>', methods=['POST'])
@admin_required
def disable_user(user_id):
    """Disable a user"""
    user = User.query.get_or_404(user_id)

    if user.email == current_user.email:
        flash('You cannot disable your own account.', 'error')
        return redirect(url_for('dashboard.user_management'))

    user.status = 'Disabled'

    try:
        db.session.commit()
        flash(f'User {user.full_name} disabled.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to disable user {user.full_name} ({user_id}): {e}")
        flash('Failed to disable user.', 'error')

    return redirect(url_for('dashboard.user_management'))

@dashboard_bp.route('/enable-user/<int:user_id>', methods=['POST'])
@admin_required
def enable_user(user_id):
    """Enable a user"""
    user = User.query.get_or_404(user_id)
    user.status = 'Active'

    try:
        db.session.commit()
        flash(f'User {user.full_name} enabled.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to enable user {user.full_name} ({user_id}): {e}")
        flash('Failed to enable user.', 'error')

    return redirect(url_for('dashboard.user_management'))

@dashboard_bp.route('/change-user-role/<int:user_id>', methods=['POST'])
@admin_required
def change_user_role(user_id):
    """Change a user's role"""
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')

    if user.email == current_user.email:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('dashboard.user_management'))

    if new_role not in ['Admin', 'Engineer', 'Automation Manager', 'PM']:
        flash('Invalid role selection.', 'error')
        return redirect(url_for('dashboard.user_management'))

    old_role = user.role
    user.role = new_role

    try:
        db.session.commit()
        flash(f'User {user.full_name} role changed from {old_role} to {new_role}.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to change role for user {user.full_name} ({user_id}): {e}")
        flash('Failed to change user role.', 'error')

    return redirect(url_for('dashboard.user_management'))

@dashboard_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user permanently"""
    user = User.query.get_or_404(user_id)

    if user.email == current_user.email:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('dashboard.user_management'))

    user_name = user.full_name
    user_email = user.email

    try:
        # Delete associated notifications first (to maintain referential integrity)
        from models import Notification
        Notification.query.filter_by(user_email=user_email).delete()

        # Delete the user
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user_name} ({user_email}) has been permanently deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete user {user_name} ({user_email}, ID: {user_id}): {e}")
        flash(f'Failed to delete user: {str(e)}', 'error')

    return redirect(url_for('dashboard.user_management'))

@dashboard_bp.route('/system-settings')
@admin_required
def system_settings():
    """System settings page"""
    company_logo = SystemSettings.get_setting('company_logo', 'static/cully.png')
    storage_location = SystemSettings.get_setting('default_storage_location', '/outputs/')

    return render_template('system_settings.html',
                         company_logo=company_logo,
                         storage_location=storage_location)

@dashboard_bp.route('/update-settings', methods=['POST'])
@admin_required
def update_settings():
    """Update system settings"""
    storage_location = request.form.get('storage_location', '').strip()

    if storage_location:
        SystemSettings.set_setting('default_storage_location', storage_location)
        flash('Settings saved successfully.', 'success')
    else:
        flash('Storage location is required.', 'error')

    return redirect(url_for('dashboard.system_settings'))

@dashboard_bp.route('/reports')
@admin_required
def admin_reports():
    """Admin reports view - show all system reports"""
    from models import Report, SATReport
    import json
    from datetime import datetime, timedelta
    
    try:
        # Calculate this month start for template
        now = datetime.now()
        this_month_start = datetime(now.year, now.month, 1)
        
        # Get all reports - don't filter, get everything
        reports = Report.query.order_by(Report.created_at.desc()).all()
        reports_data = []
        
        current_app.logger.info(f"Admin reports: Found {len(reports)} total reports in database")
        
        for report in reports:
            try:
                # Get SAT report data if it exists
                sat_report = SATReport.query.filter_by(report_id=report.id).first()
                
                # Start with basic report data
                project_name = report.document_title or 'Untitled Report'
                client_name = report.client_name or ''
                location = report.project_reference or ''
                status = 'Draft'
                
                # If SAT report exists, try to get enhanced data
                if sat_report and sat_report.data_json:
                    try:
                        stored_data = json.loads(sat_report.data_json)
                        context_data = stored_data.get('context', {})
                        
                        # Override with SAT data if available
                        if context_data.get('DOCUMENT_TITLE'):
                            project_name = context_data['DOCUMENT_TITLE']
                        if context_data.get('CLIENT_NAME'):
                            client_name = context_data['CLIENT_NAME']
                        if context_data.get('PROJECT_REFERENCE'):
                            location = context_data['PROJECT_REFERENCE']
                            
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        current_app.logger.warning(f"Could not decode SATReport data for report ID {report.id}: {e}")
                
                # Determine status from approvals
                if report.approvals_json:
                    try:
                        approvals = json.loads(report.approvals_json)
                        if approvals:
                            statuses = [a.get("status", "pending") for a in approvals]
                            if "rejected" in statuses:
                                status = "Rejected"
                            elif all(s == "approved" for s in statuses):
                                status = "Approved"
                            elif any(s == "approved" for s in statuses):
                                status = "Partially Approved"
                            else:
                                status = "Pending Review"
                        else:
                            status = "Draft"
                    except (json.JSONDecodeError, TypeError):
                        status = "Pending Review"
                else:
                    status = "Draft"
                
                # Add report to list
                reports_data.append({
                    'id': report.id,
                    'project_name': project_name,
                    'client_name': client_name,
                    'location': location,
                    'created_by': report.user_email,
                    'status': status,
                    'created_date': report.created_at
                })
                
                current_app.logger.debug(f"Processed report {report.id}: {project_name}")
                
            except Exception as report_error:
                current_app.logger.error(f"Error processing report {report.id}: {report_error}", exc_info=True)
                # Add basic report info even if processing fails
                reports_data.append({
                    'id': report.id,
                    'project_name': report.document_title or f'Report {report.id}',
                    'client_name': report.client_name or '',
                    'location': report.project_reference or '',
                    'created_by': report.user_email,
                    'status': 'Error',
                    'created_date': report.created_at
                })
        
        current_app.logger.info(f"Admin reports: Successfully processed {len(reports_data)} reports for display")
        
        return render_template('admin_reports.html', 
                             reports=reports_data,
                             this_month_start=this_month_start)
        
    except Exception as e:
        current_app.logger.error(f"Error in admin_reports function: {e}", exc_info=True)
        
        # Try to get basic report count for debugging
        try:
            report_count = Report.query.count()
            current_app.logger.info(f"Database has {report_count} reports total")
        except Exception as count_error:
            current_app.logger.error(f"Cannot even count reports: {count_error}")
            
        # Still provide this_month_start even on error
        now = datetime.now()
        this_month_start = datetime(now.year, now.month, 1)
        return render_template('admin_reports.html', 
                             reports=[],
                             this_month_start=this_month_start)

@dashboard_bp.route('/create-report')
@role_required(['Engineer'])
def create_report():
    """Create report - redirect to report type selector"""
    return redirect(url_for('reports.new'))

@dashboard_bp.route('/db-status')
@login_required
def db_status():
    """Check database connection status"""
    try:
        # Try to connect to database
        db.engine.connect().close()
        return jsonify({'status': 'connected', 'message': 'Database connection successful'})
    except Exception as e:
        current_app.logger.error(f"Database status check failed: {e}")
        return jsonify({'status': 'error', 'message': f'Database connection failed: {str(e)}'}), 500

@dashboard_bp.route('/dashboard/api/admin/users')
@admin_required
def api_admin_users():
    """API endpoint for user management data"""
    try:
        users = User.query.all()
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
                'status': user.status,
                'created_date': user.created_date.isoformat() if user.created_date else None
            })

        return jsonify({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching users: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/dashboard/api/admin/reports')
@admin_required
def api_admin_reports():
    """API endpoint for reports data"""
    try:
        reports = Report.query.order_by(Report.created_at.desc()).limit(50).all()
        reports_data = []

        for report in reports:
            # Get report title from SAT data if available
            title = 'Untitled Report'
            if hasattr(report, 'sat_report') and report.sat_report:
                try:
                    import json
                    data = json.loads(report.sat_report.data_json)
                    title = data.get('context', {}).get('DOCUMENT_TITLE', 'Untitled Report')
                except:
                    pass

            # Determine status
            status = 'pending'
            if report.approvals_json:
                try:
                    import json
                    approvals = json.loads(report.approvals_json)
                    statuses = [a.get("status", "pending") for a in approvals]
                    if "rejected" in statuses:
                        status = "rejected"
                    elif all(s == "approved" for s in statuses):
                        status = "approved"
                    elif any(s == "approved" for s in statuses):
                        status = "partially_approved"
                except:
                    pass

            reports_data.append({
                'id': report.id,
                'title': title,
                'user_email': report.user_email,
                'status': status,
                'created_at': report.created_at.isoformat() if report.created_at else None
            })

        return jsonify({
            'success': True,
            'reports': reports_data
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching reports: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/dashboard/api/admin/settings')
@admin_required
def api_admin_settings():
    """API endpoint for system settings"""
    try:
        storage_location = SystemSettings.get_setting('default_storage_location', '/outputs/')
        company_logo = SystemSettings.get_setting('company_logo', 'static/cully.png')

        return jsonify({
            'success': True,
            'settings': {
                'storage_location': storage_location,
                'company_logo': company_logo
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching settings: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/dashboard/api/admin/stats')
@admin_required
def api_admin_stats():
    """API endpoint for dashboard statistics"""
    try:
        users = User.query.all()
        total_users = len(users)
        pending_users = len([u for u in users if u.status == 'Pending'])
        total_reports = Report.query.count()

        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'pending_users': pending_users,
                'total_reports': total_reports
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching stats: {e}")
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/debug/reports')
@admin_required
def debug_reports():
    """Debug endpoint to check report data"""
    try:
        from models import Report, SATReport
        
        # Get basic report count
        total_reports = Report.query.count()
        
        # Get all reports with basic info
        reports = Report.query.all()
        report_info = []
        
        for report in reports:
            sat_report = SATReport.query.filter_by(report_id=report.id).first()
            report_info.append({
                'id': report.id,
                'type': report.type,
                'user_email': report.user_email,
                'document_title': report.document_title,
                'created_at': str(report.created_at),
                'has_sat_data': sat_report is not None
            })
        
        return jsonify({
            'success': True,
            'total_reports': total_reports,
            'reports': report_info
        })
        
    except Exception as e:
        current_app.logger.error(f"Debug reports error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@dashboard_bp.route('/revoke-approval/<report_id>', methods=['POST'])
@admin_required
def revoke_approval(report_id):
    """Revoke approval for a report"""
    from models import Report, Notification
    import json
    
    try:
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        # Get the comment from request
        data = request.get_json()
        comment = data.get('comment', '').strip()
        
        if not comment:
            return jsonify({'success': False, 'message': 'Comment is required for revocation'}), 400
        
        # Check if report has approval workflow before resetting
        current_approvals = json.loads(report.approvals_json) if report.approvals_json else []
        
        if not current_approvals:
            # If no approval workflow exists, just unlock the report
            report.locked = False
            report.status = 'DRAFT'
        else:
            # Reset approvals and unlock the report
            report.approvals_json = json.dumps([])
            report.locked = False
            report.status = 'DRAFT'
        
        # Create notification for the report creator
        try:
            Notification.create_notification(
                user_email=report.user_email,
                title='Report Approval Revoked',
                message=f'Your report "{report.document_title or "SAT Report"}" approval has been revoked by admin. Reason: {comment}',
                notification_type='approval_revoked',
                submission_id=report_id,
                action_url=f'/status/{report_id}'
            )
        except Exception as notif_error:
            current_app.logger.warning(f"Could not create notification: {notif_error}")
        
        db.session.commit()
        
        current_app.logger.info(f"Report {report_id} approval revoked by admin {current_user.email}. Reason: {comment}")
        return jsonify({
            'success': True, 
            'message': 'Report unlocked and status reset successfully. You can now edit the report.'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error revoking approval for report {report_id}: {e}")
        return jsonify({'success': False, 'message': 'Failed to revoke approval'}), 500

@dashboard_bp.route('/delete-report/<report_id>', methods=['POST'])
@admin_required
def delete_report(report_id):
    """Delete a report permanently"""
    from models import Report, SATReport
    
    try:
        # Get the report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        # Delete associated SAT report data first
        sat_report = SATReport.query.filter_by(report_id=report_id).first()
        if sat_report:
            db.session.delete(sat_report)
        
        # Delete the main report
        db.session.delete(report)
        db.session.commit()
        
        current_app.logger.info(f"Report {report_id} deleted by admin {current_user.email}")
        return jsonify({'success': True, 'message': 'Report deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting report {report_id}: {e}")
        return jsonify({'success': False, 'message': 'Failed to delete report'}), 500

@dashboard_bp.route('/my-reports')
@role_required(['Engineer'])
def my_reports():
    """View engineer's own reports"""
    from models import Report, SATReport
    import json

    # Get reports created by current user
    reports = Report.query.filter_by(user_email=current_user.email).order_by(Report.updated_at.desc()).all()

    report_list = []
    for report in reports:
        sat_report = SATReport.query.filter_by(report_id=report.id).first()
        if not sat_report:
            continue

        try:
            stored_data = json.loads(sat_report.data_json)
        except json.JSONDecodeError:
            current_app.logger.warning(f"Could not decode SATReport data for report ID: {report.id}")
            stored_data = {} # Handle malformed JSON

        try:
            approvals = json.loads(report.approvals_json) if report.approvals_json else []
        except json.JSONDecodeError:
            current_app.logger.warning(f"Could not decode approvals_json for report ID: {report.id}")
            approvals = [] # Handle malformed JSON

        # Determine overall status
        statuses = [a.get("status", "pending") for a in approvals]
        if "rejected" in statuses:
            overall_status = "rejected"
        elif all(status == "approved" for status in statuses):
            overall_status = "approved"
        elif any(status == "approved" for status in statuses):
            overall_status = "partially_approved"
        else:
            overall_status = "pending"

        report_list.append({
            "id": report.id,
            "document_title": stored_data.get("context", {}).get("DOCUMENT_TITLE", "SAT Report"),
            "client_name": stored_data.get("context", {}).get("CLIENT_NAME", ""),
            "project_reference": stored_data.get("context", {}).get("PROJECT_REFERENCE", ""),
            "created_at": report.created_at,
            "updated_at": report.updated_at,
            "status": overall_status,
            "locked": report.locked
        })

    return render_template('my_reports.html', reports=report_list)
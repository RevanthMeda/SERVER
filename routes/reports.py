from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Report, User
from auth import login_required, role_required
from utils import setup_approval_workflow_db, create_new_submission_notification, get_unread_count
import json
import uuid
from datetime import datetime

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/new')
@login_required
@role_required(['Engineer', 'Automation Manager', 'PM', 'Admin'])
def new():
    """Show report type selection page"""
    return render_template('report_selector.html')

@reports_bp.route('/new/sat')
@login_required
@role_required(['Engineer', 'Automation Manager', 'Admin'])
def new_sat():
    """SAT report creation"""
    return redirect(url_for('reports.new_sat_full'))

@reports_bp.route('/new/sat/full')
@login_required
@role_required(['Engineer', 'Automation Manager', 'Admin'])
def new_sat_full():
    """Full SAT report form"""
    try:
        import uuid
        from utils import get_unread_count
        
        # Create completely empty submission data structure for new forms
        submission_data = {
            'DOCUMENT_TITLE': '',
            'PROJECT_REFERENCE': '',
            'DOCUMENT_REFERENCE': '',
            'DATE': '',
            'CLIENT_NAME': '',
            'REVISION': '',
            'REVISION_DETAILS': '',
            'REVISION_DATE': '',
            'USER_EMAIL': current_user.email if current_user.is_authenticated else '',
            'PREPARED_BY': current_user.full_name if current_user.is_authenticated else '',
            'REVIEWED_BY_TECH_LEAD': '',
            'REVIEWED_BY_PM': '',
            'APPROVED_BY_CLIENT': '',
            'PURPOSE': '',
            'SCOPE': '',
            'RELATED_DOCUMENTS': [],
            'PRE_EXECUTION_APPROVAL': [],
            'POST_EXECUTION_APPROVAL': [],
            'PRE_TEST_REQUIREMENTS': [],
            'KEY_COMPONENTS': [],
            'IP_RECORDS': [],
            'SIGNAL_LISTS': [],
            'DIGITAL_OUTPUTS': [],
            'ANALOGUE_INPUTS': [],
            'ANALOGUE_OUTPUTS': [],
            'MODBUS_DIGITAL_LISTS': [],
            'MODBUS_ANALOGUE_LISTS': [],
            'PROCESS_TEST': [],
            'SCADA_VERIFICATION': [],
            'TRENDS_TESTING': [],
            'ALARM_LIST': []
        }
        
        # Completely clear any cached form data for new reports
        unread_count = get_unread_count()
        submission_id = str(uuid.uuid4())
        
        # Don't load wizard_data for new reports - start completely fresh        
        return render_template('SAT.html', 
                             submission_data=submission_data,
                             submission_id=submission_id,
                             unread_count=unread_count,
                             is_new_report=True)
    except Exception as e:
        current_app.logger.error(f"Error rendering SAT form: {e}")
        # Provide minimal data structure even on error
        submission_data = {}
        return render_template('SAT.html', 
                             submission_data=submission_data,
                             submission_id='',
                             unread_count=0)

@reports_bp.route('/sat/wizard')
@login_required
@role_required(['Engineer', 'Automation Manager', 'Admin'])
def sat_wizard():
    """SAT wizard route for editing existing reports"""
    try:
        from models import Report, SATReport
        import json
        from utils import get_unread_count
        
        # Get submission_id from query params (for edit mode)
        submission_id = request.args.get('submission_id')
        edit_mode = request.args.get('edit_mode', 'false').lower() == 'true'
        
        if not submission_id or not edit_mode:
            # If no submission_id, redirect to new SAT form
            return redirect(url_for('reports.new_sat_full'))
        
        # Get the report from database
        report = Report.query.get(submission_id)
        if not report:
            flash('Report not found.', 'error')
            return redirect(url_for('dashboard.home'))
        
        # Check permissions
        if report.locked:
            flash('This report is locked and cannot be edited.', 'warning')
            return redirect(url_for('status.view_status', submission_id=submission_id))
        
        # Check ownership for Engineers
        if current_user.role == 'Engineer' and report.user_email != current_user.email:
            flash('You do not have permission to edit this report.', 'error')
            return redirect(url_for('dashboard.home'))
        
        # Get SAT report data
        sat_report = SATReport.query.filter_by(report_id=submission_id).first()
        if not sat_report:
            flash('Report data not found.', 'error')
            return redirect(url_for('dashboard.home'))
        
        # Parse the stored data
        try:
            stored_data = json.loads(sat_report.data_json)
            context_data = stored_data.get('context', {})
        except:
            context_data = {}
        
        # Get unread notifications count
        unread_count = get_unread_count()
        
        # Render the SAT form with existing data for editing
        return render_template('SAT.html',
                             submission_data=context_data,
                             submission_id=submission_id,
                             unread_count=unread_count,
                             user_role=current_user.role if hasattr(current_user, 'role') else 'user',
                             edit_mode=True,
                             is_new_report=False)
                             
    except Exception as e:
        current_app.logger.error(f"Error in sat_wizard: {e}", exc_info=True)
        flash('An error occurred while loading the report for editing.', 'error')
        return redirect(url_for('dashboard.home'))
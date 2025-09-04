from flask import Blueprint, render_template, redirect, url_for, flash, current_app, send_file
import os
import json
import tempfile
import shutil
from flask_login import current_user, login_required
import datetime as dt

status_bp = Blueprint('status', __name__)

@status_bp.route('/<submission_id>')
@login_required
def view_status(submission_id):
    """View a specific submission with auto-download"""
    from models import Report, SATReport

    # Check if submission_id is valid
    if not submission_id or submission_id == 'None':
        flash('Invalid submission ID.', 'error')
        return redirect(url_for('dashboard.home'))

    report = Report.query.filter_by(id=submission_id).first()
    if not report:
        flash('Report not found.', 'error')
        return redirect(url_for('dashboard.home'))

    sat_report = SATReport.query.filter_by(report_id=report.id).first()
    if not sat_report:
        flash('Report data not found.', 'error')
        return redirect(url_for('dashboard.home'))

    try:
        stored_data = json.loads(sat_report.data_json) if sat_report.data_json else {}
    except json.JSONDecodeError:
        stored_data = {}

    approvals = json.loads(report.approvals_json) if report.approvals_json else []

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

    # Get submission data context with fallbacks
    submission_data = stored_data.get("context", {})
    if not submission_data:
        submission_data = stored_data  # Fallback if context doesn't exist

    # Check if report files exist
    pdf_path = os.path.join(current_app.config['OUTPUT_DIR'], f'SAT_Report_{submission_id}_Final.pdf')
    docx_path = os.path.join(current_app.config['OUTPUT_DIR'], f'SAT_Report_{submission_id}_Final.docx')

    download_available = os.path.exists(pdf_path) or os.path.exists(docx_path)
    has_pdf = os.path.exists(pdf_path)

    # Determine if current user can edit this report
    can_edit = False
    if current_user.role == 'Admin':
        can_edit = True  # Admin can edit any report
    elif current_user.role == 'Engineer' and current_user.email == report.user_email:
        # Engineers can edit their own reports until approved by Automation Manager
        tm_approved = any(a.get("status") == "approved" and a.get("stage") == 1 for a in approvals)
        can_edit = not tm_approved
    elif current_user.role == 'Automation Manager':
        # Automation Manager can edit reports until approved by PM
        pm_approved = any(a.get("status") == "approved" and a.get("stage") == 2 for a in approvals)
        can_edit = not pm_approved

    # Build context similar to old version
    context = {
        "submission_id": submission_id,
        "submission_data": submission_data,
        "approvals": approvals,
        "locked": report.locked,
        "can_edit": can_edit,
        "created_at": report.created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(report.created_at, dt.datetime) else report.created_at,
        "updated_at": report.updated_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(report.updated_at, dt.datetime) else report.updated_at,
        "user_email": report.user_email,
        "document_title": submission_data.get("DOCUMENT_TITLE", "SAT Report"),
        "project_reference": submission_data.get("PROJECT_REFERENCE", ""),
        "client_name": submission_data.get("CLIENT_NAME", ""),
        "prepared_by": submission_data.get("PREPARED_BY", ""),
        "overall_status": overall_status,
        "download_available": download_available,
        "has_pdf": has_pdf,
        "auto_download": True
    }

    return render_template('status.html', **context)

@status_bp.route('/download/<submission_id>')
@login_required
def download_report(submission_id):
    """Download the generated report"""
    try:
        # Validate submission ID
        if not submission_id or submission_id == 'None':
            current_app.logger.error(f"Invalid submission ID: {submission_id}")
            flash('Invalid submission ID.', 'error')
            return redirect(url_for('dashboard.home'))

        # Check if we already have a generated file first (bypass database if needed)
        permanent_path = os.path.join(current_app.config['OUTPUT_DIR'], f'SAT_Report_{submission_id}_Final.docx')
        
        if os.path.exists(permanent_path):
            current_app.logger.info(f"Found existing report file: {permanent_path}")
            try:
                # Try to get document title from database, but don't fail if database is down
                from models import Report, SATReport
                report = Report.query.filter_by(id=submission_id).first()
                if report:
                    sat_report = SATReport.query.filter_by(report_id=submission_id).first()
                    if sat_report and sat_report.data_json:
                        stored_data = json.loads(sat_report.data_json)
                        context_data = stored_data.get("context", {})
                        doc_title = context_data.get("DOCUMENT_TITLE", "SAT_Report")
                    else:
                        doc_title = "SAT_Report"
                else:
                    doc_title = "SAT_Report"
            except Exception as db_error:
                current_app.logger.warning(f"Database error when getting title, using default: {db_error}")
                doc_title = "SAT_Report"
            
            # Get project number for filename (SAT_PROJNUMBER format)
            project_number = context_data.get("PROJECT_REFERENCE", "").strip()
            if not project_number:
                project_number = context_data.get("PROJECT_NUMBER", "").strip()
            if not project_number:
                project_number = submission_id[:8]  # Fallback to submission ID
                
            # Clean project number for filename  
            safe_proj_num = "".join(c if c.isalnum() or c in ['_', '-'] else "_" for c in project_number)
            download_name = f"SAT_{safe_proj_num}.docx"
            
            # Ensure file is not corrupted and has proper headers
            if not os.path.exists(permanent_path) or os.path.getsize(permanent_path) < 1000:
                current_app.logger.error(f"Existing file is corrupted or too small: {permanent_path}")
                flash('Report file is corrupted. Please regenerate.', 'error')
                return redirect(url_for('status.view_status', submission_id=submission_id))
            
            current_app.logger.info(f"Serving existing file: {permanent_path} as {download_name}")
            
            # Return with proper Word document headers
            return send_file(
                permanent_path, 
                as_attachment=True, 
                download_name=download_name,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

        # If file doesn't exist, try to get data from database and generate
        try:
            from models import Report, SATReport
            report = Report.query.filter_by(id=submission_id).first()
            if not report:
                current_app.logger.error(f"Report not found in database: {submission_id}")
                flash('Report not found in database.', 'error')
                return redirect(url_for('dashboard.home'))

            sat_report = SATReport.query.filter_by(report_id=submission_id).first()
            if not sat_report:
                current_app.logger.error(f"SAT report data not found: {submission_id}")
                flash('Report data not found.', 'error')
                return redirect(url_for('dashboard.home'))

            # Parse stored data
            try:
                stored_data = json.loads(sat_report.data_json) if sat_report.data_json else {}
            except json.JSONDecodeError as json_error:
                current_app.logger.error(f"JSON decode error: {json_error}")
                stored_data = {}

            context_data = stored_data.get("context", {})
            if not context_data:
                current_app.logger.error(f"No context data found for submission: {submission_id}")
                flash('No report data found.', 'error')
                return redirect(url_for('status.view_status', submission_id=submission_id))

        except Exception as db_error:
            current_app.logger.error(f"Database error: {db_error}")
            flash('Database connection error. Cannot generate report.', 'error')
            return redirect(url_for('dashboard.home'))

        # Generate fresh report
        current_app.logger.info(f"Generating fresh report for submission {submission_id}")

        try:
            # Check template file exists
            template_file = current_app.config.get('TEMPLATE_FILE', 'templates/SAT_Template.docx')
            if not os.path.exists(template_file):
                current_app.logger.error(f"Template file not found: {template_file}")
                flash('Report template file not found.', 'error')
                return redirect(url_for('status.view_status', submission_id=submission_id))

            # Initialize DocxTemplate with clean environment
            from docxtpl import DocxTemplate, InlineImage
            from docx.shared import Mm
            import copy
            
            # Create a fresh template instance to avoid cached issues
            doc = DocxTemplate(template_file)

            # Process signatures from stored data
            SIG_PREPARED = ""
            if context_data.get("prepared_signature"):
                sig_path = os.path.join(current_app.config['SIGNATURES_FOLDER'], context_data["prepared_signature"])
                if os.path.exists(sig_path):
                    try:
                        SIG_PREPARED = InlineImage(doc, sig_path, width=Mm(40))
                    except Exception as e:
                        current_app.logger.error(f"Error loading signature: {e}")

            # Process stored images
            def load_stored_images(url_list, max_width_mm=150):
                """Load stored images from URLs"""
                image_objects = []
                upload_dir = os.path.join(current_app.config['UPLOAD_ROOT'], submission_id)

                if not os.path.exists(upload_dir):
                    current_app.logger.warning(f"Upload directory not found: {upload_dir}")
                    return image_objects

                for url in url_list:
                    try:
                        # Extract filename from URL
                        filename = url.split('/')[-1]
                        image_path = os.path.join(upload_dir, filename)

                        if os.path.exists(image_path):
                            try:
                                from PIL import Image
                                with Image.open(image_path) as img:
                                    w, h = img.size

                                # Calculate scale to fit max width
                                scale = min(1, max_width_mm / (w * 0.264583))

                                image_objects.append(
                                    InlineImage(doc, image_path,
                                        width=Mm(w * 0.264583 * scale),
                                        height=Mm(h * 0.264583 * scale)
                                    )
                                )
                            except Exception as e:
                                current_app.logger.error(f"Error processing stored image {filename}: {e}")
                                # Add default size if image processing fails
                                try:
                                    image_objects.append(
                                        InlineImage(doc, image_path, width=Mm(100), height=Mm(80))
                                    )
                                except Exception as e2:
                                    current_app.logger.error(f"Failed to add image with default size: {e2}")
                        else:
                            current_app.logger.warning(f"Image file not found: {image_path}")
                    except Exception as e:
                        current_app.logger.error(f"Error loading stored image from {url}: {e}")

                return image_objects

            # Load stored images safely
            try:
                scada_urls = json.loads(sat_report.scada_image_urls) if sat_report.scada_image_urls else []
                trends_urls = json.loads(sat_report.trends_image_urls) if sat_report.trends_image_urls else []
                alarm_urls = json.loads(sat_report.alarm_image_urls) if sat_report.alarm_image_urls else []
            except Exception as json_error:
                current_app.logger.error(f"Error parsing image URLs: {json_error}")
                scada_urls = trends_urls = alarm_urls = []

            scada_image_objects = load_stored_images(scada_urls)
            trends_image_objects = load_stored_images(trends_urls)
            alarm_image_objects = load_stored_images(alarm_urls)

            # Build context for template rendering
            render_context = dict(context_data)
            render_context.update({
                "SIG_PREPARED": SIG_PREPARED,
                "SCADA_IMAGES": scada_image_objects,
                "TRENDS_IMAGES": trends_image_objects,
                "ALARM_IMAGES": alarm_image_objects,
                "SIG_APPROVER_1": "",
                "SIG_APPROVER_2": "",
                "SIG_APPROVER_3": "",
            })

            # Render the document with proper error handling
            try:
                doc.render(render_context)
                
                # Ensure output directory exists
                permanent_dir = current_app.config['OUTPUT_DIR']
                os.makedirs(permanent_dir, exist_ok=True)
                
                # Save document and create a clean copy
                try:
                    # First save to temporary file
                    temp_doc_path = permanent_path + '.temp'
                    doc.save(temp_doc_path)
                    current_app.logger.info(f"Initial document save completed: {temp_doc_path}")
                    
                    # Now create a clean copy by re-opening and re-saving with python-docx
                    # This removes any DocxTemplate artifacts and creates a clean Word document
                    from docx import Document
                    clean_doc = Document(temp_doc_path)
                    clean_doc.save(permanent_path)
                    
                    # Remove temp file
                    if os.path.exists(temp_doc_path):
                        os.remove(temp_doc_path)
                        
                    current_app.logger.info(f"Clean document created: {permanent_path}")
                    
                except Exception as save_error:
                    current_app.logger.error(f"Document save failed: {save_error}")
                    # Clean up temp file if it exists
                    temp_path = permanent_path + '.temp'
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                    raise Exception(f"Failed to save document: {save_error}")
                
                # Verify file was created and has reasonable size
                if not os.path.exists(permanent_path):
                    raise Exception("Document file was not created")
                    
                file_size = os.path.getsize(permanent_path)
                if file_size < 1000:  # Word docs should be at least 1KB
                    raise Exception(f"Document file too small ({file_size} bytes) - likely corrupted")
                    
                current_app.logger.info(f"Document verified: {permanent_path} ({file_size} bytes)")
                
                # Verify the file was created and has content
                if not os.path.exists(permanent_path) or os.path.getsize(permanent_path) == 0:
                    raise Exception("Document file was not created properly or is empty")
                    
                current_app.logger.info(f"Document saved successfully: {permanent_path} ({os.path.getsize(permanent_path)} bytes)")
                
            except Exception as render_error:
                current_app.logger.error(f"Error rendering/saving document: {render_error}", exc_info=True)
                flash(f'Error generating report document: {str(render_error)}', 'error')
                return redirect(url_for('status.view_status', submission_id=submission_id))

            current_app.logger.info(f"Fresh report generated: {permanent_path}")

            # Get project number for filename (SAT_PROJNUMBER format)
            project_number = context_data.get("PROJECT_REFERENCE", "").strip()
            if not project_number:
                project_number = context_data.get("PROJECT_NUMBER", "").strip()
            if not project_number:
                project_number = submission_id[:8]  # Fallback to submission ID
                
            # Clean project number for filename
            safe_proj_num = "".join(c if c.isalnum() or c in ['_', '-'] else "_" for c in project_number)
            download_name = f"SAT_{safe_proj_num}.docx"

            # Verify file exists and has proper size before sending
            if not os.path.exists(permanent_path) or os.path.getsize(permanent_path) == 0:
                flash('Error: Generated document is empty or corrupted.', 'error')
                return redirect(url_for('status.view_status', submission_id=submission_id))

            current_app.logger.info(f"Serving file: {permanent_path} as {download_name}")
            
            # Create a final clean copy for download to ensure portability
            final_download_path = os.path.join(tempfile.mkdtemp(), download_name)
            
            try:
                # Create completely clean document for download
                from docx import Document
                final_doc = Document(permanent_path)
                final_doc.save(final_download_path)
                
                current_app.logger.info(f"Final clean document created for download: {final_download_path}")
                
                # Return the clean file with proper headers
                response = send_file(
                    final_download_path, 
                    as_attachment=True, 
                    download_name=download_name,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                
                # Add headers for better compatibility
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache" 
                response.headers["Expires"] = "0"
                response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{download_name}"
                
                return response
                
            except Exception as final_error:
                current_app.logger.error(f"Error creating final clean document: {final_error}")
                # If all else fails, serve the original file
                return send_file(
                    permanent_path, 
                    as_attachment=True, 
                    download_name=download_name,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )

        except Exception as generation_error:
            current_app.logger.error(f"Error during report generation: {generation_error}", exc_info=True)
            flash('Error generating report for download.', 'error')
            return redirect(url_for('status.view_status', submission_id=submission_id))

    except Exception as e:
        current_app.logger.error(f"Error in download_report for {submission_id}: {e}", exc_info=True)
        flash('Error downloading report.', 'error')
        return redirect(url_for('dashboard.home'))



@status_bp.route('/list')
@login_required
def list_submissions():
    """List all submissions for admin view"""
    from models import Report, SATReport

    try:
        reports = Report.query.order_by(Report.created_at.desc()).all()
        submission_list = []

        for report in reports:
            sat_report = SATReport.query.filter_by(report_id=report.id).first()
            if not sat_report:
                continue

            try:
                stored_data = json.loads(sat_report.data_json)
            except json.JSONDecodeError:
                stored_data = {}

            # Determine overall status
            if report.approvals_json:
                try:
                    approvals = json.loads(report.approvals_json)
                    statuses = [a.get("status", "pending") for a in approvals]
                    if "rejected" in statuses:
                        overall_status = "rejected"
                    elif all(status == "approved" for status in statuses):
                        overall_status = "approved"
                    elif any(status == "approved" for status in statuses):
                        overall_status = "partially_approved"
                    else:
                        overall_status = "pending"
                except:
                    overall_status = "pending"
            else:
                overall_status = "draft"

            submission_list.append({
                "id": report.id,
                "document_title": stored_data.get("context", {}).get("DOCUMENT_TITLE", "SAT Report"),
                "client_name": stored_data.get("context", {}).get("CLIENT_NAME", ""),
                "created_at": report.created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(report.created_at, dt.datetime) else report.created_at,
                "updated_at": report.updated_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(report.updated_at, dt.datetime) else report.updated_at,
                "status": overall_status,
                "user_email": report.user_email
            })

        return render_template('submissions_list.html', submissions=submission_list)

    except Exception as e:
        current_app.logger.error(f"Error fetching submissions list: {e}")
        flash('Error loading submissions.', 'error')
        return render_template('submissions_list.html', submissions=[])
#!/usr/bin/env python
"""
Fix PENDING reports that are incorrectly locked
This script updates the database to ensure:
- PENDING reports have locked=False
- Only APPROVED reports have locked=True
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from app import create_app
from models import db, Report

# Create the Flask app
app = create_app('default')

def fix_report_locks():
    """Fix the locked status for all reports based on their approval status"""
    
    with app.app_context():
        print("Starting report lock fix...")
        print("=" * 50)
        
        # Get all reports
        all_reports = Report.query.all()
        print(f"Found {len(all_reports)} total reports")
        
        fixed_count = 0
        already_correct = 0
        
        for report in all_reports:
            old_locked = report.locked
            old_status = report.status
            
            # Determine what the locked status should be
            should_be_locked = False
            
            # Check if report is APPROVED
            if report.status == 'APPROVED':
                should_be_locked = True
            # Check approval stages to see if Automation Manager has approved
            elif report.approvals_json:
                try:
                    approvals = json.loads(report.approvals_json)
                    # Check if stage 1 (Automation Manager) has approved
                    for approval in approvals:
                        if approval.get('stage') == 1 and approval.get('status') == 'approved':
                            should_be_locked = True
                            break
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Fix the locked status if needed
            if report.locked != should_be_locked:
                report.locked = should_be_locked
                fixed_count += 1
                print(f"  Fixed Report {report.id}:")
                print(f"    Status: {report.status}")
                print(f"    Locked: {old_locked} -> {should_be_locked}")
                print(f"    Title: {report.document_title or 'Untitled'}")
            else:
                already_correct += 1
        
        # Commit all changes
        if fixed_count > 0:
            db.session.commit()
            print(f"\n✓ Successfully fixed {fixed_count} reports")
        
        print(f"✓ {already_correct} reports were already correct")
        
        # Show summary
        print("\n" + "=" * 50)
        print("Summary of report statuses after fix:")
        
        # Count by status
        status_counts = {}
        locked_counts = {'locked': 0, 'unlocked': 0}
        
        for report in Report.query.all():
            status = report.status or 'DRAFT'
            status_counts[status] = status_counts.get(status, 0) + 1
            if report.locked:
                locked_counts['locked'] += 1
            else:
                locked_counts['unlocked'] += 1
        
        print("\nBy Status:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count} reports")
        
        print("\nBy Lock Status:")
        print(f"  Locked: {locked_counts['locked']} reports")
        print(f"  Unlocked: {locked_counts['unlocked']} reports")
        
        # Show specific PENDING reports
        pending_reports = Report.query.filter_by(status='PENDING').all()
        if pending_reports:
            print(f"\nPENDING Reports ({len(pending_reports)} total):")
            for report in pending_reports[:5]:  # Show first 5
                print(f"  - {report.id}: locked={report.locked}, title='{report.document_title or 'Untitled'}'")
            if len(pending_reports) > 5:
                print(f"  ... and {len(pending_reports) - 5} more")
        
        print("\n✓ Database fix completed successfully!")

if __name__ == '__main__':
    fix_report_locks()
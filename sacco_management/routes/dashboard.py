import io
import pandas as pd
from flask import Blueprint, render_template, make_response
from flask_login import login_required
from models import db, Member, Deposit, Loan, AuditLog
from sqlalchemy import func
from utils import role_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    total_members = Member.query.count()
    # Optimized Database Math (fixes the memory leak issue)
    total_savings = db.session.query(func.sum(Deposit.amount)).filter(Deposit.deposit_type == 'Savings').scalar() or 0.0
    
    approved_loans = Loan.query.filter_by(status='Approved').all()
    total_loans_disbursed = sum(l.principal for l in approved_loans)
    
    pending_loans_count = Loan.query.filter_by(status='Pending').count()
    recent_members = Member.query.order_by(Member.date_joined.desc()).limit(5).all()

    return render_template('index.html', total_members=total_members, total_savings=total_savings, 
                           total_loans_disbursed=total_loans_disbursed, pending_loans_count=pending_loans_count, 
                           recent_members=recent_members)


@dashboard_bp.route('/export/members')
@login_required
def export_members():
    members = Member.query.all()
    
    # Structure data for Pandas
    data = []
    for m in members:
        data.append({
            'Member No': m.member_no,
            'Full Name': m.full_name,
            'National ID': m.national_id,
            'Phone': m.phone,
            'Total Savings (KES)': m.total_savings,
            'Share Capital (KES)': m.total_share_capital,
            'Active Loans (KES)': m.active_loans_total
        })
        
    df = pd.DataFrame(data)
    out = io.BytesIO()
    
    # Write to Excel in memory
    writer = pd.ExcelWriter(out, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='SACCO_Members')
    writer.close()
    
    # Create the HTTP response to force file download
    response = make_response(out.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=sacco_members_report.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

@dashboard_bp.route('/logs')
@login_required
@role_required('Admin') # Only Admins can view the system logs
def system_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template('logs.html', logs=logs)
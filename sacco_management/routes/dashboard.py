from flask import Blueprint, render_template
from flask_login import login_required
from models import Member, Deposit, Loan
from sqlalchemy import func
from models import db

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
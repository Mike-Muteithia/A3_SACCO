from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import FinancialTransaction, Member, Loan
from utils import permission_required

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/journal')
@login_required
@permission_required('REPORT_READ_ALL') # RBAC: Manager / SystemAdmin
def consolidated_journal():
    transactions = FinancialTransaction.query.order_by(FinancialTransaction.date.desc()).limit(500).all()
    return render_template('journal.html', transactions=transactions)

@reports_bp.route('/reports/statement/<int:member_id>')
@login_required
def member_statement(member_id):
    # RBAC: Members can only view their own statement
    if current_user.role.name == 'Member' and current_user.member_id != member_id:
        flash('Access Denied: You can only view your own financial statements.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    member = Member.query.get_or_404(member_id)
    return render_template('statement.html', member=member)

@reports_bp.route('/reports/outstanding-loans')
@login_required
@permission_required('REPORT_READ_ALL')
def outstanding_loans():
    active_loans = Loan.query.filter_by(status='Approved').all()
    portfolio_at_risk = sum(l.remaining_balance for l in active_loans)
    return render_template('outstanding_loans.html', loans=active_loans, par=portfolio_at_risk)
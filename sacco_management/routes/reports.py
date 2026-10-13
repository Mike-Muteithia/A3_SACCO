from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import FinancialTransaction, Member, Loan
from utils import permission_required

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/journal')
@login_required
@permission_required('REPORT_READ_ALL') # RBAC: Manager / SystemAdmin
def consolidated_journal():
    page = request.args.get('page', 1, type=int)
    # Fetch data in chunks of 50
    transactions = FinancialTransaction.query.order_by(FinancialTransaction.date.desc()).paginate(page=page, per_page=50)
    return render_template('journal.html', transactions=transactions)

@reports_bp.route('/reports/statement/<int:member_id>')
@login_required
def member_statement(member_id):
    # Enforce Segregation of Duties: Customers access ONLY their ID; Staff MUST possess REPORT_READ_ALL
    if current_user.role.name == 'Member':
        if current_user.member_id != member_id:
            flash('Access Denied: Insecure Object Reference blocked.', 'danger')
            return redirect(url_for('dashboard.index'))
    elif not current_user.has_permission('REPORT_READ_ALL'):
        flash('Access Denied: Missing REPORT_READ_ALL authorization.', 'danger')
        return redirect(url_for('dashboard.index'))
    member = db.session.query(Member).get_or_404(member_id)
    return render_template('statement.html', member=member)

@reports_bp.route('/reports/outstanding-loans')
@login_required
@permission_required('REPORT_READ_ALL')
def outstanding_loans():
    active_loans = Loan.query.filter_by(status='Approved').all()
    portfolio_at_risk = sum(l.remaining_balance for l in active_loans)
    return render_template('outstanding_loans.html', loans=active_loans, par=portfolio_at_risk)
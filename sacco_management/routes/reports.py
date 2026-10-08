from flask import Blueprint, render_template
from flask_login import login_required
from models import FinancialTransaction
from utils import permission_required

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/journal')
@login_required
@permission_required('REPORT_READ_ALL') # RBAC: Manager / SystemAdmin
def consolidated_journal():
    transactions = FinancialTransaction.query.order_by(FinancialTransaction.date.desc()).limit(500).all()
    return render_template('journal.html', transactions=transactions)
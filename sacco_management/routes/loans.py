from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Loan, Member, LoanRepayment, AuditLog
from forms import LoanForm, RepaymentForm
from utils import role_required

loans_bp = Blueprint('loans', __name__)

@loans_bp.route('/loans', methods=['GET', 'POST'])
@login_required
def index():
    form = LoanForm()
    form.member_id.choices = [(m.id, f"{m.member_no} - {m.full_name}") for m in Member.query.all()]

    if form.validate_on_submit():
        member = Member.query.get(form.member_id.data)
        max_eligible = member.total_savings * 3
        
        if member.total_savings <= 0:
            flash('Member has no savings. Ineligible for loans.', 'danger')
        elif form.principal.data > max_eligible:
            flash(f'Loan exceeds 3x multiplier limit (Max KES {max_eligible:,.2f}).', 'warning')
        else:
            loan = Loan(member_id=member.id, principal=form.principal.data, duration_months=int(form.duration_months.data))
            db.session.add(loan)
            db.session.commit()
            flash('Loan application submitted.', 'success')
            return redirect(url_for('loans.index'))

    loans = Loan.query.order_by(Loan.application_date.desc()).all()
    return render_template('loans.html', form=form, loans=loans)

# Notice the RBAC decorator here! Only Admin or LoanOfficer can approve/reject
@loans_bp.route('/loans/<int:loan_id>/<action>')
@login_required
@role_required('LoanOfficer')
def action(loan_id, action):
    loan = Loan.query.get_or_404(loan_id)
    if loan.status != 'Pending':
        flash('Action denied. Loan is already locked.', 'danger')
        return redirect(url_for('loans.index'))

    if action == 'approve':
        loan.status = 'Approved'
        flash(f'Loan #{loan.id} approved.', 'success')
    elif action == 'reject':
        loan.status = 'Rejected'
        flash(f'Loan #{loan.id} rejected.', 'warning')

    log = AuditLog(
        user_id=current_user.id,
        action=f"Marked Loan #{loan.id} as {loan.status}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    return redirect(url_for('loans.index'))


@loans_bp.route('/loans/<int:loan_id>/repay', methods=['GET', 'POST'])
@login_required
def repay(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if loan.status != 'Approved':
        flash('Can only make repayments on Approved loans.', 'danger')
        return redirect(url_for('loans.index'))
        
    form = RepaymentForm()
    if form.validate_on_submit():
        if form.amount.data > loan.remaining_balance:
            flash(f'Amount exceeds remaining balance of KES {loan.remaining_balance:,.2f}', 'warning')
        else:
            repayment = LoanRepayment(loan_id=loan.id, amount=form.amount.data, reference=form.reference.data)
            db.session.add(repayment)
            
            # Automatically settle the loan if balance is cleared
            if (loan.remaining_balance - form.amount.data) <= 0.01:
                loan.status = 'Settled'
                
            db.session.commit()
            flash('Repayment recorded successfully.', 'success')
            return redirect(url_for('loans.repay', loan_id=loan.id))
            
    repayments = LoanRepayment.query.filter_by(loan_id=loan.id).order_by(LoanRepayment.date.desc()).all()
    return render_template('loan_repay.html', loan=loan, form=form, repayments=repayments)
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Loan, Member, LoanRepayment, AuditLog
from forms import LoanForm, RepaymentForm

loans_bp = Blueprint('loans', __name__)

@loans_bp.route('/loans', methods=['GET', 'POST'])
@login_required
def index():
    form = LoanForm()
    
    # RBAC: Members only see themselves; Staff see everyone
    if current_user.role.name == 'Member':
        form.member_id.choices = [(m.id, f"{m.member_no} - {m.full_name}") for m in Member.query.filter_by(id=current_user.member_id).all()]
        loans = Loan.query.filter_by(member_id=current_user.member_id).order_by(Loan.application_date.desc()).all()
    else:
        form.member_id.choices = [(m.id, f"{m.member_no} - {m.full_name}") for m in Member.query.all()]
        loans = Loan.query.order_by(Loan.application_date.desc()).all()

    if form.validate_on_submit():
        member = Member.query.get(form.member_id.data)
        max_eligible = member.total_savings * 3
        
        if member.total_savings <= 0:
            flash('Ineligible for loans (No savings).', 'danger')
        elif form.principal.data > max_eligible:
            flash(f'Loan exceeds 3x limit (Max KES {max_eligible:,.2f}).', 'warning')
        else:
            loan = Loan(member_id=member.id, principal=form.principal.data, duration_months=int(form.duration_months.data))
            db.session.add(loan)
            db.session.commit()
            flash('Loan application submitted.', 'success')
            return redirect(url_for('loans.index'))
            
    return render_template('loans.html', form=form, loans=loans)

@loans_bp.route('/loans/<int:loan_id>/<action>')
@login_required
def action(loan_id, action):
    loan = Loan.query.get_or_404(loan_id)
    
    # RBAC: Tiered Approval Logic
    if loan.principal > 500000:
        if not current_user.has_permission('LOAN_APPROVE_LARGE'):
            flash('Large loans (>KES 500,000) require Manager approval.', 'danger')
            return redirect(url_for('loans.index'))
    else:
        if not current_user.has_permission('LOAN_APPROVE_STD') and not current_user.has_permission('LOAN_APPROVE_LARGE'):
            flash('Access Denied. You cannot approve standard loans.', 'danger')
            return redirect(url_for('loans.index'))

    if loan.status != 'Pending':
        flash('Loan is already locked.', 'danger')
        return redirect(url_for('loans.index'))

    if action == 'approve':
        loan.status = 'Approved'
        flash(f'Loan #{loan.id} approved.', 'success')
    elif action == 'reject':
        loan.status = 'Rejected'
        flash(f'Loan #{loan.id} rejected.', 'warning')
        
    db.session.add(AuditLog(user_id=current_user.id, action=f"Marked Loan #{loan.id} as {loan.status}", ip_address=request.remote_addr))
    db.session.commit()
    return redirect(url_for('loans.index'))

@loans_bp.route('/loans/<int:loan_id>/repay', methods=['GET', 'POST'])
@login_required
def repay(loan_id):
    # (Keep existing repayment logic from Current State)
    loan = Loan.query.get_or_404(loan_id)
    form = RepaymentForm()
    if form.validate_on_submit():
        repayment = LoanRepayment(loan_id=loan.id, amount=form.amount.data, reference=form.reference.data)
        db.session.add(repayment)
        if (loan.remaining_balance - form.amount.data) <= 0.01:
            loan.status = 'Settled'
        db.session.commit()
        flash('Repayment recorded.', 'success')
        return redirect(url_for('loans.repay', loan_id=loan.id))
    repayments = LoanRepayment.query.filter_by(loan_id=loan.id).order_by(LoanRepayment.date.desc()).all()
    return render_template('loan_repay.html', loan=loan, form=form, repayments=repayments)
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, FinancialTransaction, Member, AuditLog
from forms import TransactionForm
from utils import permission_required

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/transactions', methods=['GET', 'POST'])
@login_required
@permission_required('TX_CREATE') # Teller Permission
def index():
    form = TransactionForm()
    # Populate the dropdown dynamically (Active members only)
    form.member_id.choices = [(m.id, f"{m.member_no} - {m.full_name}") for m in Member.query.filter_by(is_active=True).order_by(Member.full_name).all()]
    
    if form.validate_on_submit():
        # Lock the member row until this transaction commits/rolls back
        member = Member.query.with_for_update().get(form.member_id.data)
        
        # Prevent overdrafts on withdrawals
        if form.transaction_type.data == 'Withdrawal' and form.amount.data > member.total_savings:
            flash(f'Insufficient savings. Available balance: KES {member.total_savings:,.2f}', 'danger')
            return redirect(url_for('transactions.index'))
            
        tx = FinancialTransaction(
            member_id=form.member_id.data, 
            transaction_type=form.transaction_type.data,
            amount=form.amount.data, 
            reference=form.reference.data
        )
        db.session.add(tx)
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action=f"Recorded {tx.transaction_type} of KES {tx.amount} for Member ID {tx.member_id}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        try:
            db.session.commit()
            flash('Transaction recorded successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('A database error occurred. Transaction rolled back.', 'danger')
            
        return redirect(url_for('transactions.index'))
        
    transactions = FinancialTransaction.query.order_by(FinancialTransaction.date.desc()).limit(50).all()
    return render_template('transactions.html', transactions=transactions, form=form)
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Deposit, Member, AuditLog
from forms import DepositForm

deposits_bp = Blueprint('deposits', __name__)

@deposits_bp.route('/deposits', methods=['GET', 'POST'])
@login_required
def index():
    form = DepositForm()
    # Populate the dropdown dynamically from the database
    form.member_id.choices = [(m.id, f"{m.member_no} - {m.full_name}") for m in Member.query.order_by(Member.full_name).all()]

    if form.validate_on_submit():
        deposit = Deposit(
            member_id=form.member_id.data,
            deposit_type=form.deposit_type.data,
            amount=form.amount.data,
            reference=form.reference.data
        )
        db.session.add(deposit)

        log = AuditLog(
            user_id=current_user.id,
            action=f"Recorded {deposit.deposit_type} of KES {deposit.amount} for Member ID {deposit.member_id}",
            ip_address=request.remote_addr
        )
        db.session.add(log)

        db.session.commit()
        flash('Deposit recorded successfully.', 'success')
        return redirect(url_for('deposits.index'))

    deposit_records = Deposit.query.order_by(Deposit.date.desc()).limit(50).all()
    return render_template('deposits.html', deposits=deposit_records, form=form)
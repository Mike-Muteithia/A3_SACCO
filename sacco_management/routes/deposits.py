from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from models import db, Deposit, Member
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
            amount=form.amount.data,
            reference=form.reference.data
        )
        db.session.add(deposit)
        db.session.commit()
        flash('Deposit recorded successfully.', 'success')
        return redirect(url_for('deposits.index'))

    deposit_records = Deposit.query.order_by(Deposit.date.desc()).limit(50).all()
    return render_template('deposits.html', deposits=deposit_records, form=form)
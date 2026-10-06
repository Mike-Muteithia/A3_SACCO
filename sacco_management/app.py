import os
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Member, Deposit, Loan

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sacco-dev-secret-key-xyz'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sacco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def dashboard():
    total_members = Member.query.count()
    all_deposits = Deposit.query.all()
    total_savings = sum(d.amount for d in all_deposits)
    
    approved_loans = Loan.query.filter_by(status='Approved').all()
    total_loans_disbursed = sum(l.principal for l in approved_loans)
    
    pending_loans_count = Loan.query.filter_by(status='Pending').count()
    recent_members = Member.query.order_by(Member.date_joined.desc()).limit(5).all()

    return render_template(
        'index.html',
        total_members=total_members,
        total_savings=total_savings,
        total_loans_disbursed=total_loans_disbursed,
        pending_loans_count=pending_loans_count,
        recent_members=recent_members
    )

@app.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        member_no = request.form['member_no'].strip()
        full_name = request.form['full_name'].strip()
        national_id = request.form['national_id'].strip()
        phone = request.form['phone'].strip()
        email = request.form.get('email', '').strip()

        if Member.query.filter((Member.member_no == member_no) | (Member.national_id == national_id)).first():
            flash('Member Number or National ID already exists.', 'danger')
        else:
            new_member = Member(member_no=member_no, full_name=full_name, national_id=national_id, phone=phone, email=email)
            db.session.add(new_member)
            db.session.commit()
            flash('Member registered successfully!', 'success')
            return redirect(url_for('members'))

    member_list = Member.query.order_by(Member.id.desc()).all()
    return render_template('members.html', members=member_list)

@app.route('/deposits', methods=['GET', 'POST'])
def deposits():
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        amount = float(request.form.get('amount', 0))
        reference = request.form.get('reference', '').strip()

        if amount <= 0:
            flash('Deposit amount must be greater than zero.', 'danger')
        else:
            deposit = Deposit(member_id=member_id, amount=amount, reference=reference)
            db.session.add(deposit)
            db.session.commit()
            flash('Deposit recorded successfully.', 'success')
            return redirect(url_for('deposits'))

    all_members = Member.query.order_by(Member.full_name).all()
    deposit_records = Deposit.query.order_by(Deposit.date.desc()).limit(50).all()
    return render_template('deposits.html', members=all_members, deposits=deposit_records)

@app.route('/loans', methods=['GET', 'POST'])
def loans():
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        principal = float(request.form.get('principal', 0))
        duration = int(request.form.get('duration_months', 12))
        
        member = Member.query.get(member_id)
        # Sacco rule: Loan cannot exceed 3x total savings
        max_eligible = member.total_savings * 3
        if member.total_savings <= 0:
            flash('Member has no savings. Ineligible for loans.', 'danger')
        elif principal > max_eligible:
            flash(f'Loan exceeds 3x multiplier limit (Max allowable: KES {max_eligible:,.2f}).', 'warning')
        else:
            loan = Loan(member_id=member_id, principal=principal, duration_months=duration, status='Pending')
            db.session.add(loan)
            db.session.commit()
            flash('Loan application submitted for review.', 'success')
            return redirect(url_for('loans'))

    all_members = Member.query.order_by(Member.full_name).all()
    all_loans = Loan.query.order_by(Loan.application_date.desc()).all()
    return render_template('loans.html', members=all_members, loans=all_loans)

@app.route('/loans/<int:loan_id>/<action>')
def loan_action(loan_id, action):
    loan = Loan.query.get_or_404(loan_id)
    if action == 'approve':
        loan.status = 'Approved'
        flash(f'Loan #{loan.id} approved.', 'success')
    elif action == 'reject':
        loan.status = 'Rejected'
        flash(f'Loan #{loan.id} rejected.', 'warning')
    db.session.commit()
    return redirect(url_for('loans'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
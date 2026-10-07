from app import create_app
from models import db, Member, Deposit, Loan, User, LoanRepayment, AuditLog
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def seed_database():
    app = create_app()
    with app.app_context():
        print("Clearing existing data...")
        db.drop_all()
        db.create_all()

        print("Creating Staff Users...")
        admin = User(username='admin', password_hash=generate_password_hash('admin123'), role='Admin')
        officer = User(username='loanofficer', password_hash=generate_password_hash('loan123'), role='LoanOfficer')
        teller = User(username='teller', password_hash=generate_password_hash('teller123'), role='Teller')
        db.session.add_all([admin, officer, teller])
        db.session.commit()

        print("Adding SACCO Members...")
        m1 = Member(member_no='M001', full_name='Kamau Njoroge', national_id='11223344', phone='0711223344', email='kamau@example.com')
        m2 = Member(member_no='M002', full_name='Aisha Patel', national_id='22334455', phone='0722334455', email='aisha@example.com')
        m3 = Member(member_no='M003', full_name='Brian Ochieng', national_id='33445566', phone='0733445566', email='brian@example.com')
        m4 = Member(member_no='M004', full_name='Joy Mutuku', national_id='44556677', phone='0744556677', email='joy@example.com')
        m5 = Member(member_no='M005', full_name='David Wanjala', national_id='55667788', phone='0755667788', email='david@example.com')
        db.session.add_all([m1, m2, m3, m4, m5])
        db.session.commit()

        print("Recording Deposits (Savings & Share Capital)...")
        deposits = [
            Deposit(member_id=m1.id, deposit_type='Share Capital', amount=5000, reference='SHR001'),
            Deposit(member_id=m1.id, deposit_type='Savings', amount=15000, reference='DEP001'),
            Deposit(member_id=m2.id, deposit_type='Share Capital', amount=10000, reference='SHR002'),
            Deposit(member_id=m2.id, deposit_type='Savings', amount=45000, reference='DEP002'),
            Deposit(member_id=m3.id, deposit_type='Share Capital', amount=2000, reference='SHR003'),
            Deposit(member_id=m3.id, deposit_type='Savings', amount=8000, reference='DEP003'),
            Deposit(member_id=m4.id, deposit_type='Share Capital', amount=5000, reference='SHR004'),
            Deposit(member_id=m4.id, deposit_type='Savings', amount=25000, reference='DEP004'),
            Deposit(member_id=m5.id, deposit_type='Savings', amount=10000, reference='DEP005')
        ]
        db.session.add_all(deposits)
        db.session.commit()

        print("Generating Loans...")
        # Kamau: Approved and partially repaid
        l1 = Loan(member_id=m1.id, principal=30000, duration_months=12, status='Approved')
        # Aisha: Applied for large loan, currently pending
        l2 = Loan(member_id=m2.id, principal=100000, duration_months=24, status='Pending')
        # Brian: Rejected due to exceeding 3x limit
        l3 = Loan(member_id=m3.id, principal=50000, duration_months=6, status='Rejected')
        # Joy: Fully repaid, marking as Settled
        l4 = Loan(member_id=m4.id, principal=40000, duration_months=12, status='Settled')
        db.session.add_all([l1, l2, l3, l4])
        db.session.commit()

        print("Simulating Repayments...")
        repayments = [
            LoanRepayment(loan_id=l1.id, amount=10000, reference='REP001'),
            LoanRepayment(loan_id=l1.id, amount=5000, reference='REP002'),
            LoanRepayment(loan_id=l4.id, amount=l4.total_payable, reference='REP003') # Joy clears balance
        ]
        db.session.add_all(repayments)
        db.session.commit()

        print("Generating System Audit Logs...")
        logs = [
            AuditLog(user_id=teller.id, action='Recorded Savings of KES 15000.0 for Member ID 1', ip_address='192.168.1.10'),
            AuditLog(user_id=teller.id, action='Recorded Share Capital of KES 5000.0 for Member ID 1', ip_address='192.168.1.10'),
            AuditLog(user_id=officer.id, action='Marked Loan #1 as Approved', ip_address='192.168.1.12'),
            AuditLog(user_id=officer.id, action='Marked Loan #3 as Rejected', ip_address='192.168.1.12'),
            AuditLog(user_id=teller.id, action='Recorded Repayment of KES 10000.0 for Loan #1', ip_address='192.168.1.10'),
            AuditLog(user_id=admin.id, action='System initialized and seeded with commercial testing data', ip_address='127.0.0.1')
        ]
        db.session.add_all(logs)
        db.session.commit()

        print("✅ Database successfully seeded with commercial testing data!")

if __name__ == '__main__':
    seed_database()
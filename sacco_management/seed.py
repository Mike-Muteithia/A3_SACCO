from app import app
from models import db, Member, Deposit, Loan
from datetime import datetime, timedelta

def seed_database():
    with app.app_context():
        print("Clearing existing data...")
        db.drop_all()
        db.create_all()

        print("Adding Members...")
        m1 = Member(member_no='M001', full_name='Kamau Njoroge', national_id='11223344', phone='0711223344', email='kamau@example.com')
        m2 = Member(member_no='M002', full_name='Aisha Patel', national_id='22334455', phone='0722334455', email='aisha@example.com')
        m3 = Member(member_no='M003', full_name='Brian Ochieng', national_id='33445566', phone='0733445566', email='brian@example.com')
        m4 = Member(member_no='M004', full_name='Joy Mutuku', national_id='44556677', phone='0744556677', email='joy@example.com')
        
        db.session.add_all([m1, m2, m3, m4])
        db.session.commit()

        print("Recording Deposits...")
        # Kamau: Total 20,000
        d1 = Deposit(member_id=m1.id, amount=15000, reference='RKG12A34B5')
        d2 = Deposit(member_id=m1.id, amount=5000, reference='RKG98C76D5')
        # Aisha: Total 45,000
        d3 = Deposit(member_id=m2.id, amount=45000, reference='RKG55E44F3')
        # Brian: Total 8,000
        d4 = Deposit(member_id=m3.id, amount=8000, reference='RKG11G22H9')
        # Joy has no deposits yet

        db.session.add_all([d1, d2, d3, d4])
        db.session.commit()

        print("Generating Loans...")
        # Kamau has 20k savings -> eligible for 60k. Applied for 30k (Approved)
        l1 = Loan(member_id=m1.id, principal=30000, duration_months=12, status='Approved')
        
        # Aisha has 45k savings -> eligible for 135k. Applied for 100k (Pending)
        l2 = Loan(member_id=m2.id, principal=100000, duration_months=24, status='Pending')
        
        # Brian has 8k savings -> eligible for 24k. Applied for 50k (Rejected - Exceeds 3x limit)
        l3 = Loan(member_id=m3.id, principal=50000, duration_months=6, status='Rejected')

        db.session.add_all([l1, l2, l3])
        db.session.commit()

        print("✅ Database successfully seeded with testing data!")

if __name__ == '__main__':
    seed_database()
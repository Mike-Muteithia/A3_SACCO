from app import create_app
from models import db, Member, FinancialTransaction, Loan, User, Role, Permission
from werkzeug.security import generate_password_hash
from faker import Faker

def seed_database():
    app = create_app()
    with app.app_context():
        # Reset database
        db.drop_all()
        db.create_all()
        
        # 1. Recreate Permissions
        perms = {
            'PROFILE_READ': Permission(name='PROFILE_READ'),
            'PROFILE_DELETE': Permission(name='PROFILE_DELETE'),
            'TX_CREATE': Permission(name='TX_CREATE'),
            'LOAN_APPROVE_STD': Permission(name='LOAN_APPROVE_STD'),
            'LOAN_APPROVE_LARGE': Permission(name='LOAN_APPROVE_LARGE'),
            'REPORT_READ_ALL': Permission(name='REPORT_READ_ALL'),
            'SYSTEM_CONFIG': Permission(name='SYSTEM_CONFIG'),
            'USER_MANAGE': Permission(name='USER_MANAGE'),
            'OWN_READ': Permission(name='OWN_READ')
        }
        db.session.add_all(perms.values())
        
        # 2. Recreate Roles
        roles = {
            'Member': Role(name='Member', permissions=[perms['OWN_READ']]),
            'Teller': Role(name='Teller', permissions=[perms['PROFILE_READ'], perms['TX_CREATE']]),
            'LoanOfficer': Role(name='LoanOfficer', permissions=[perms['PROFILE_READ'], perms['LOAN_APPROVE_STD']]),
            'Manager': Role(name='Manager', permissions=[perms['PROFILE_READ'], perms['LOAN_APPROVE_STD'], perms['LOAN_APPROVE_LARGE'], perms['REPORT_READ_ALL']]),
            'SystemAdmin': Role(name='SystemAdmin', permissions=[perms['SYSTEM_CONFIG'], perms['PROFILE_DELETE'], perms['USER_MANAGE'], perms['PROFILE_READ']])
        }
        db.session.add_all(roles.values())
        db.session.commit()
        
        # 3. Seed Staff Users
        db.session.add(User(username='teller_01', password_hash=generate_password_hash('pass123'), role_id=roles['Teller'].id))
        db.session.add(User(username='officer_01', password_hash=generate_password_hash('pass123'), role_id=roles['LoanOfficer'].id))
        db.session.add(User(username='manager_01', password_hash=generate_password_hash('pass123'), role_id=roles['Manager'].id))
        db.session.add(User(username='admin_01', password_hash=generate_password_hash('pass123'), role_id=roles['SystemAdmin'].id))
        
        # 4. Generate 25 Dummy Members
        fake = Faker()
        print("Generating 25 dummy members for pagination testing...")
        
        for i in range(1, 26):
            m = Member(
                member_no=f'M{i:03d}',
                full_name=fake.name(),
                national_id=str(fake.unique.random_number(digits=8, fix_len=True)),
                phone=fake.numerify(text='07########'),
                email=fake.email()
            )
            db.session.add(m)
            
            # Link the first member to a generic customer login
            if i == 1:
                db.session.flush() # Flush to get the member ID before committing
                db.session.add(User(username='member_01', password_hash=generate_password_hash('pass123'), role_id=roles['Member'].id, member_id=m.id))

        db.session.commit()
        print("Database seeded successfully with RBAC matrix, staff accounts, and dummy members.")

if __name__ == '__main__':
    seed_database()
from app import create_app
from models import db, Member, FinancialTransaction, Loan, User, Role, Permission
from werkzeug.security import generate_password_hash

def seed_database():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        
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

        roles = {
            'Member': Role(name='Member', permissions=[perms['OWN_READ']]),
            'Teller': Role(name='Teller', permissions=[perms['PROFILE_READ'], perms['TX_CREATE']]),
            'LoanOfficer': Role(name='LoanOfficer', permissions=[perms['PROFILE_READ'], perms['LOAN_APPROVE_STD']]),
            'Manager': Role(name='Manager', permissions=[perms['PROFILE_READ'], perms['LOAN_APPROVE_STD'], perms['LOAN_APPROVE_LARGE'], perms['REPORT_READ_ALL']]),
            'SystemAdmin': Role(name='SystemAdmin', permissions=[perms['SYSTEM_CONFIG'], perms['PROFILE_DELETE'], perms['USER_MANAGE']])
        }
        db.session.add_all(roles.values())
        db.session.commit()

        # Seed Customer
        m1 = Member(member_no='M001', full_name='Kamau Njoroge', national_id='112233', phone='0711', email='kamau@example.com')
        db.session.add(m1)
        db.session.commit()

        # Seed Users mapped to Roles
        db.session.add(User(username='teller_01', password_hash=generate_password_hash('pass123'), role_id=roles['Teller'].id))
        db.session.add(User(username='officer_01', password_hash=generate_password_hash('pass123'), role_id=roles['LoanOfficer'].id))
        db.session.add(User(username='manager_01', password_hash=generate_password_hash('pass123'), role_id=roles['Manager'].id))
        db.session.add(User(username='admin_01', password_hash=generate_password_hash('pass123'), role_id=roles['SystemAdmin'].id))
        
        # Link customer login to Member profile
        db.session.add(User(username='kamau', password_hash=generate_password_hash('pass123'), role_id=roles['Member'].id, member_id=m1.id))
        db.session.commit()
        
        print("Database seeded with strictly normalized RBAC matrix & accounts.")

if __name__ == '__main__':
    seed_database()
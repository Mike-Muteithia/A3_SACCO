from app import create_app
from models import db, Member, FinancialTransaction, Loan, User, Role, Permission
from werkzeug.security import generate_password_hash

def seed_database():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # 1. Define Granular Permissions
        perms = {
            'PROFILE_READ': Permission(name='PROFILE_READ'),
            'PROFILE_DELETE': Permission(name='PROFILE_DELETE'),
            'TX_CREATE': Permission(name='TX_CREATE'),
            'LOAN_APPROVE_STD': Permission(name='LOAN_APPROVE_STD'),
            'LOAN_APPROVE_LARGE': Permission(name='LOAN_APPROVE_LARGE'),
            'REPORT_READ_ALL': Permission(name='REPORT_READ_ALL'),
            'SYSTEM_CONFIG': Permission(name='SYSTEM_CONFIG')
        }
        db.session.add_all(perms.values())

        # 2. Strict RBAC Matrix Enforcement
        roles = {
            'Member': Role(name='Member', permissions=[perms['PROFILE_READ']]),
            'Teller': Role(name='Teller', permissions=[perms['PROFILE_READ'], perms['TX_CREATE']]),
            'LoanOfficer': Role(name='LoanOfficer', permissions=[perms['PROFILE_READ'], perms['LOAN_APPROVE_STD']]),
            'Manager': Role(name='Manager', permissions=[perms['PROFILE_READ'], perms['LOAN_APPROVE_STD'], perms['LOAN_APPROVE_LARGE'], perms['REPORT_READ_ALL']]),
            'SystemAdmin': Role(name='SystemAdmin', permissions=[perms['SYSTEM_CONFIG'], perms['PROFILE_DELETE']])
        }
        db.session.add_all(roles.values())
        db.session.commit()

        # 3. Seed Users mapped to Roles
        db.session.add(User(username='teller_01', password_hash=generate_password_hash('pass123'), role_id=roles['Teller'].id))
        db.session.add(User(username='officer_01', password_hash=generate_password_hash('pass123'), role_id=roles['LoanOfficer'].id))
        db.session.add(User(username='manager_01', password_hash=generate_password_hash('pass123'), role_id=roles['Manager'].id))
        db.session.add(User(username='admin_01', password_hash=generate_password_hash('pass123'), role_id=roles['SystemAdmin'].id))
        db.session.commit()
        
        print("Database seeded with strictly normalized RBAC matrix.")

if __name__ == '__main__':
    seed_database()
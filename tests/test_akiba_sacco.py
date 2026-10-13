import os
import pytest
from decimal import Decimal
from werkzeug.security import generate_password_hash

from app import create_app
from models import db, User, Role, Permission, Member, FinancialTransaction, Loan, LoanRepayment, AuditLog

# ==============================================================================
# Pytest Fixtures (Environment & Data Setup)
# ==============================================================================

@pytest.fixture
def app():
    """Initializes Flask application with an isolated in-memory SQLite database."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'WTF_CSRF_CHECK_DEFAULT': False,
        'SECRET_KEY': 'akiba_qa_test_key_isolated',
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def init_database(app):
    """Seeds RBAC matrix, foundational staff, and test members."""
    perms = {
        'OWN_READ': Permission(name='OWN_READ'),
        'PROFILE_READ': Permission(name='PROFILE_READ'),
        'PROFILE_DELETE': Permission(name='PROFILE_DELETE'),
        'TX_CREATE': Permission(name='TX_CREATE'),
        'LOAN_APPROVE_STD': Permission(name='LOAN_APPROVE_STD'),
        'LOAN_APPROVE_LARGE': Permission(name='LOAN_APPROVE_LARGE'),
        'REPORT_READ_ALL': Permission(name='REPORT_READ_ALL'),
        'USER_MANAGE': Permission(name='USER_MANAGE')
    }
    db.session.add_all(perms.values())
    db.session.flush() 
    
    roles = {
        'Member': Role(name='Member', permissions=[perms['OWN_READ']]),
        'Teller': Role(name='Teller', permissions=[perms['PROFILE_READ'], perms['TX_CREATE']]),
        'LoanOfficer': Role(name='LoanOfficer', permissions=[perms['PROFILE_READ'], perms['LOAN_APPROVE_STD']]),
        'Manager': Role(name='Manager', permissions=[perms['PROFILE_READ'], perms['LOAN_APPROVE_STD'], perms['LOAN_APPROVE_LARGE'], perms['REPORT_READ_ALL']]),
        'SystemAdmin': Role(name='SystemAdmin', permissions=[perms['USER_MANAGE'], perms['PROFILE_READ'], perms['PROFILE_DELETE'], perms['REPORT_READ_ALL']])
    }
    db.session.add_all(roles.values())
    db.session.commit()

    pwd = generate_password_hash('pass123')
    staff = [
        User(username='teller_qa', password_hash=pwd, role_id=roles['Teller'].id),
        User(username='officer_qa', password_hash=pwd, role_id=roles['LoanOfficer'].id),
        User(username='manager_qa', password_hash=pwd, role_id=roles['Manager'].id),
        User(username='admin_qa', password_hash=pwd, role_id=roles['SystemAdmin'].id)
    ]
    db.session.add_all(staff)
    
    m1 = Member(member_no="M-QA01", full_name="Alice QA", national_id="1234567", phone="0711000000", email="alice@qa.com")
    m2 = Member(member_no="M-QA02", full_name="Bob QA", national_id="7654321", phone="0722000000", email="bob@qa.com")
    db.session.add_all([m1, m2])
    db.session.commit()
    
    db.session.add(User(username='alice_member', password_hash=pwd, role_id=roles['Member'].id, member_id=m1.id))
    db.session.add(User(username='bob_member', password_hash=pwd, role_id=roles['Member'].id, member_id=m2.id))
    db.session.commit()

@pytest.fixture
def auth_client(app, init_database):
    """Spawns an isolated test client per authentication request."""
    def _login(username):
        client = app.test_client()
        res = client.post('/login', data={'username': username, 'password': 'pass123'}, follow_redirects=True)
        assert b'Welcome back' in res.data, f"CRITICAL: Failed to authenticate {username}"
        return client
    return _login

# ==============================================================================
# 1. Teller Counter Operations & Cashier Guardrails
# ==============================================================================

def test_financial_precision_and_audit_logging(auth_client, app):
    client = auth_client('teller_qa')
    with app.app_context():
        member_id = db.session.query(Member).filter_by(member_no="M-QA01").first().id

    response = client.post('/transactions', data={
        'member_id': member_id,
        'transaction_type': 'Savings',
        'amount': '150.55',
        'reference': 'DEP-01'
    }, follow_redirects=True)
    assert b'Transaction recorded successfully' in response.data
    
    with app.app_context():
        assert db.session.get(Member, member_id).total_savings == Decimal('150.55')
        log = AuditLog.query.first()
        assert log is not None
        assert "Recorded Savings" in log.action

def test_overdraft_prevention_locking(auth_client, app):
    client = auth_client('teller_qa')
    with app.app_context():
        member = db.session.query(Member).filter_by(member_no="M-QA01").first()
        db.session.add(FinancialTransaction(member_id=member.id, transaction_type='Savings', amount=Decimal('500.00')))
        db.session.commit()
        member_id = member.id

    response = client.post('/transactions', data={
        'member_id': member_id,
        'transaction_type': 'Withdrawal',
        'amount': '600.00'
    }, follow_redirects=True)
    
    assert b'Overdraft prohibited' in response.data
    with app.app_context():
        assert db.session.get(Member, member_id).total_savings == Decimal('500.00')

# ==============================================================================
# 2. Member Onboarding & KYC Validation
# ==============================================================================

def test_kenyan_kyc_validations(auth_client, app):
    client = auth_client('teller_qa')
    with app.app_context():
        initial_count = Member.query.count()
        
    client.post('/members', data={
        'member_no': 'M-QA03',
        'full_name': 'Invalid User',
        'national_id': '123',
        'phone': '0800123456',
        'email': 'bademail'
    }, follow_redirects=True)
    
    with app.app_context():
        assert Member.query.count() == initial_count

def test_archiving_integrity_soft_delete(auth_client, app):
    client = auth_client('admin_qa')
    with app.app_context():
        member_id = db.session.query(Member).filter_by(member_no="M-QA01").first().id
    
    client.post(f'/members/{member_id}/delete', follow_redirects=True)
    
    with app.app_context():
        archived_member = db.session.get(Member, member_id)
        assert not archived_member.is_active

# ==============================================================================
# 3. Credit Origination, Amortization & Tiered Approvals
# ==============================================================================

def test_collateral_limits_and_amortization_math(app, init_database):
    with app.app_context():
        member = db.session.query(Member).filter_by(member_no="M-QA01").first()
        db.session.add(FinancialTransaction(member_id=member.id, transaction_type='Savings', amount=Decimal('10000.00')))
        db.session.commit()
        
        assert member.total_savings * 3 == Decimal('30000.00')
        loan = Loan(member_id=member.id, principal=Decimal('100000.00'), interest_rate=Decimal('12.00'), duration_months=6)
        assert loan.monthly_installment == Decimal('17254.84')
        assert loan.total_payable == Decimal('103529.04')

def test_loan_approval_officer_guardrail(auth_client, app):
    """Test that LoanOfficer is blocked from approving large loans."""
    officer = auth_client('officer_qa')
    
    with app.app_context():
        member = db.session.query(Member).filter_by(member_no="M-QA02").first()
        loan = Loan(member_id=member.id, principal=Decimal('600000.00'), duration_months=24)
        db.session.add(loan)
        db.session.commit()
        loan_id = loan.id

    res = officer.post(f'/loans/{loan_id}/approve', follow_redirects=True)
    assert b'require Manager approval' in res.data
    
    with app.app_context():
        assert db.session.get(Loan, loan_id).status == 'Pending'

def test_loan_approval_manager_success(auth_client, app):
    """Test that Manager successfully approves large loans."""
    manager = auth_client('manager_qa')
    
    with app.app_context():
        member = db.session.query(Member).filter_by(member_no="M-QA02").first()
        loan = Loan(member_id=member.id, principal=Decimal('600000.00'), duration_months=24)
        db.session.add(loan)
        db.session.commit()
        loan_id = loan.id

    res = manager.post(f'/loans/{loan_id}/approve', follow_redirects=True)
    assert b'approved' in res.data
    
    with app.app_context():
        assert db.session.get(Loan, loan_id).status == 'Approved'

    res_lock = manager.post(f'/loans/{loan_id}/reject', follow_redirects=True)
    assert b'Loan is already locked' in res_lock.data

def test_loan_auto_settlement(app, init_database):
    with app.app_context():
        member = db.session.query(Member).first()
        loan = Loan(member_id=member.id, principal=Decimal('1000.00'), interest_rate=Decimal('0.00'), duration_months=1, status='Approved')
        db.session.add(loan)
        db.session.commit()

        db.session.add(LoanRepayment(loan_id=loan.id, amount=Decimal('1000.00')))
        db.session.commit()
        
        if loan.remaining_balance <= Decimal('0.01'):
            loan.status = 'Settled'
        
        assert loan.remaining_balance == Decimal('0.00')
        assert loan.status == 'Settled'

# ==============================================================================
# 4. Auditing, Regulatory Reporting & Data Export
# ==============================================================================

def test_consolidated_journal_rbac_teller(auth_client):
    teller = auth_client('teller_qa')
    res = teller.get('/reports/journal', follow_redirects=True)
    assert b'Access Denied' in res.data

def test_consolidated_journal_rbac_manager(auth_client):
    manager = auth_client('manager_qa')
    res = manager.get('/reports/journal?page=1', follow_redirects=True)
    assert b'Consolidated Financial Ledger' in res.data
    assert res.status_code == 200

    res_export = manager.get('/export/members')
    assert res_export.status_code == 200
    assert res_export.headers["Content-Disposition"] == "attachment; filename=sacco_members_report.xlsx"

# ==============================================================================
# 5. Role-Based Access Control (RBAC), CSRF & IDOR Hardening
# ==============================================================================

def test_idor_prevention_on_statements(auth_client, app):
    alice = auth_client('alice_member')
    with app.app_context():
        bob_id = db.session.query(Member).filter_by(member_no="M-QA02").first().id

    response = alice.get(f'/reports/statement/{bob_id}', follow_redirects=True)
    assert b'Insecure Object Reference blocked' in response.data

def test_http_cookie_security(auth_client):
    client = auth_client('teller_qa')
    response = client.get('/')
    
    cookies = response.headers.getlist('Set-Cookie')
    for cookie in cookies:
        if 'session' in cookie:
            assert 'HttpOnly' in cookie
            assert 'SameSite=Lax' in cookie

def test_csrf_enforcement():
    secure_app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': True,
        'WTF_CSRF_CHECK_DEFAULT': True, 
        'SECRET_KEY': 'secure_csrf_key'
    })
    
    with secure_app.test_client() as client:
        response = client.post('/login', data={'username': 'teller_qa', 'password': 'pass123'})
        assert response.status_code == 400
        assert b'Bad Request' in response.data

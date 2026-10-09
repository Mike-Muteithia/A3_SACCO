from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import func

db = SQLAlchemy()

# Normalized RBAC Mapping
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.relationship('Permission', secondary=role_permissions, lazy='subquery')

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    role = db.relationship('Role')
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=True) # Links customer login to profile

    def has_permission(self, perm_name):
        return any(p.name == perm_name for p in self.role.permissions)

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    member_no = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    transactions = db.relationship('FinancialTransaction', backref='member', lazy=True, cascade="all, delete-orphan")
    loans = db.relationship('Loan', backref='member', lazy=True, cascade="all, delete-orphan")

    @property
    def total_savings(self):
        deposits = sum(t.amount for t in self.transactions if t.transaction_type == 'Savings')
        withdraws = sum(t.amount for t in self.transactions if t.transaction_type == 'Withdrawal')
        return deposits - withdraws

    @property
    def active_loans_total(self):
        return sum(l.principal for l in self.loans if l.status == 'Approved')

    @property
    def total_savings(self):
        deposits = db.session.query(func.coalesce(func.sum(FinancialTransaction.amount), 0)).filter_by(member_id=self.id, transaction_type='Savings').scalar()
        withdraws = db.session.query(func.coalesce(func.sum(FinancialTransaction.amount), 0)).filter_by(member_id=self.id, transaction_type='Withdrawal').scalar()
        return deposits - withdraws

    @property
    def active_loans_total(self):
        return db.session.query(func.coalesce(func.sum(Loan.principal), 0)).filter_by(member_id=self.id, status='Approved').scalar()

class FinancialTransaction(db.Model):
    __tablename__ = 'financial_transactions'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False) # Savings, Share Capital, Withdrawal
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    reference = db.Column(db.String(50), nullable=True)

class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    principal = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=12.0)
    duration_months = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    repayments = db.relationship('LoanRepayment', backref='loan', lazy=True, cascade="all, delete-orphan")

    @property
    def remaining_balance(self):
        r = (self.interest_rate / 100) / 12
        n = self.duration_months
        installment = self.principal / n if r == 0 else (self.principal * r * (1 + r)**n) / ((1 + r)**n - 1)
        total_payable = installment * self.duration_months
        
        # Calculate total repaid via SQL
        total_repaid = db.session.query(func.coalesce(func.sum(LoanRepayment.amount), 0)).filter_by(loan_id=self.id).scalar()
        
        return total_payable - total_repaid

class LoanRepayment(db.Model):
    __tablename__ = 'loan_repayments'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    reference = db.Column(db.String(50), nullable=True)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='logs', lazy=True)
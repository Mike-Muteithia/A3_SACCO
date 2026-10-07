from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Teller') # Admin, LoanOfficer, Teller


class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    member_no = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    
    deposits = db.relationship('Deposit', backref='member', lazy=True, cascade="all, delete-orphan")
    loans = db.relationship('Loan', backref='member', lazy=True, cascade="all, delete-orphan")

    @property
    def total_savings(self):
        return sum(d.amount for d in self.deposits if d.deposit_type == 'Savings')
        
    @property
    def total_share_capital(self):
        return sum(d.amount for d in self.deposits if d.deposit_type == 'Share Capital')

    @property
    def active_loans_total(self):
        return sum(l.principal for l in self.loans if l.status == 'Approved')

class Deposit(db.Model):
    __tablename__ = 'deposits'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    deposit_type = db.Column(db.String(20), nullable=False, default='Savings') # Savings or Share Capital
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    reference = db.Column(db.String(50), nullable=True)

class LoanRepayment(db.Model):
    __tablename__ = 'loan_repayments'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
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
    def monthly_installment(self):
        # Amortized reducing balance calculation
        r = (self.interest_rate / 100) / 12
        n = self.duration_months
        if r == 0:
            return self.principal / n
        return (self.principal * r * (1 + r)**n) / ((1 + r)**n - 1)

    @property
    def total_payable(self):
        return self.monthly_installment * self.duration_months
        
    @property
    def total_repaid(self):
        return sum(r.amount for r in self.repayments)
        
    @property
    def remaining_balance(self):
        return self.total_payable - self.total_repaid
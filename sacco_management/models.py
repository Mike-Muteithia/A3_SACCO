from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    member_no = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    deposits = db.relationship('Deposit', backref='member', lazy=True, cascade="all, delete-orphan")
    loans = db.relationship('Loan', backref='member', lazy=True, cascade="all, delete-orphan")

    @property
    def total_savings(self):
        return sum(d.amount for d in self.deposits)

    @property
    def active_loans_total(self):
        return sum(l.principal for l in self.loans if l.status == 'Approved')

class Deposit(db.Model):
    __tablename__ = 'deposits'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    reference = db.Column(db.String(50), nullable=True)

class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    principal = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=12.0)  # e.g., 12% per annum
    duration_months = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected, Settled
    application_date = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def total_payable(self):
        # Flat rate calculation: Principal + (Principal * Rate * Time / 100)
        return self.principal + (self.principal * (self.interest_rate / 100) * (self.duration_months / 12))
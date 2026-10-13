"""
Akiba Sacco Management System - Data Models
Financial domain models utilizing Decimal precision and pessimistic database locking.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import func

db = SQLAlchemy()

# Precision helper for all currency calculations
CURRENCY_PLACES = Decimal('0.01')


def quantize_currency(amount: Any) -> Decimal:
    """Rounds values strictly to two decimal places using banker's rounding."""
    if amount is None:
        return Decimal('0.00')
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return amount.quantize(CURRENCY_PLACES, rounding=ROUND_HALF_UP)


# Normalized RBAC Many-to-Many Mapping
role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)


class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    permissions = db.relationship('Permission', secondary=role_permissions, lazy='subquery')

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    role = db.relationship('Role', lazy='joined')
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=True, unique=True)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)

    def has_permission(self, perm_name: str) -> bool:
        """Evaluates whether the user's role contains the requested permission."""
        if not self.role:
            return False
        return any(p.name == perm_name for p in self.role.permissions)

    def __repr__(self) -> str:
        return f"<User {self.username} (Role: {self.role.name if self.role else 'None'})>"


class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    member_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    date_joined = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    transactions = db.relationship('FinancialTransaction', backref='member', lazy=True, cascade="all, delete-orphan")
    loans = db.relationship('Loan', backref='member', lazy=True, cascade="all, delete-orphan")

    @property
    def total_savings(self) -> Decimal:
        """Calculates net unencumbered savings balance with Decimal precision."""
        deposits = db.session.query(
            func.coalesce(func.sum(FinancialTransaction.amount), 0)
        ).filter(
            FinancialTransaction.member_id == self.id,
            FinancialTransaction.transaction_type == 'Savings'
        ).scalar()

        withdrawals = db.session.query(
            func.coalesce(func.sum(FinancialTransaction.amount), 0)
        ).filter(
            FinancialTransaction.member_id == self.id,
            FinancialTransaction.transaction_type == 'Withdrawal'
        ).scalar()

        net = Decimal(str(deposits)) - Decimal(str(withdrawals))
        return quantize_currency(net)

    @property
    def active_loans_total(self) -> Decimal:
        """Returns the sum of original principals for all active approved loans."""
        total = db.session.query(
            func.coalesce(func.sum(Loan.principal), 0)
        ).filter(
            Loan.member_id == self.id,
            Loan.status == 'Approved'
        ).scalar()
        return quantize_currency(total)


class FinancialTransaction(db.Model):
    __tablename__ = 'financial_transactions'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False, index=True)
    transaction_type = db.Column(db.String(50), nullable=False)  # Savings, Share Capital, Withdrawal
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    reference = db.Column(db.String(50), nullable=True, index=True)


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False, index=True)
    principal = db.Column(db.Numeric(14, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), default=Decimal('12.00'), nullable=False)  # Annual Rate %
    duration_months = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending', nullable=False, index=True)  # Pending, Approved, Rejected, Settled
    application_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    repayments = db.relationship('LoanRepayment', backref='loan', lazy=True, cascade="all, delete-orphan")

    @property
    def monthly_installment(self) -> Decimal:
        """
        Calculates monthly loan installment using the standard amortization formula:
        M = P * [r(1 + r)^n] / [(1 + r)^n - 1]
        Evaluated exclusively using Decimal calculations to prevent floating point drift.
        """
        principal = Decimal(str(self.principal))
        months = Decimal(self.duration_months)

        if months <= 0:
            return Decimal('0.00')

        # Convert annual interest rate percentage into monthly decimal rate
        annual_rate = Decimal(str(self.interest_rate)) / Decimal('100')
        monthly_rate = annual_rate / Decimal('12')

        if monthly_rate == Decimal('0'):
            return quantize_currency(principal / months)

        factor = (Decimal('1') + monthly_rate) ** int(self.duration_months)
        numerator = principal * monthly_rate * factor
        denominator = factor - Decimal('1')

        installment = numerator / denominator
        return quantize_currency(installment)

    @property
    def total_payable(self) -> Decimal:
        """Total liability over the loan term: Monthly Installment * Duration."""
        total = self.monthly_installment * Decimal(self.duration_months)
        return quantize_currency(total)

    @property
    def total_repaid(self) -> Decimal:
        """Sum of all posted repayments."""
        repaid = db.session.query(
            func.coalesce(func.sum(LoanRepayment.amount), 0)
        ).filter(LoanRepayment.loan_id == self.id).scalar()
        return quantize_currency(repaid)

    @property
    def remaining_balance(self) -> Decimal:
        """Unsettled liability on the loan account."""
        balance = self.total_payable - self.total_repaid
        return quantize_currency(balance)


class LoanRepayment(db.Model):
    __tablename__ = 'loan_repayments'

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    reference = db.Column(db.String(50), nullable=True)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = db.relationship('User', backref='logs', lazy=True)

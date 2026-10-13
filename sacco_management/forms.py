from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, SelectField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Regexp, Length

class LoginForm(FlaskForm):
    username = StringField('Staff / Member Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In Securely')

class MemberForm(FlaskForm):
    member_no = StringField('Member Number', validators=[
        DataRequired(),
        Regexp(r'^[A-Z0-9_-]{3,20}$', message="Member number must be alphanumeric (3-20 chars).")
    ])
    full_name = StringField('Full Official Name', validators=[DataRequired(), Length(min=3, max=100)])
    national_id = StringField('Kenyan National ID', validators=[
        DataRequired(),
        Regexp(r'^[1-9]\d{6,7}$', message="Enter a valid 7 or 8-digit Kenyan National ID.")
    ])
    phone = StringField('Mobile Number (M-Pesa)', validators=[
        DataRequired(),
        Regexp(r'^(?:\+254|0)(?:7[0-9]|1[0-1])[0-9]{7}$', message="Valid formats: 07XXXXXXXX, 01XXXXXXXX, or +2547XXXXXXXX.")
    ])
    email = StringField('Email Address', validators=[Optional(), Email()])
    submit = SubmitField('Register Member')

class TransactionForm(FlaskForm):
    member_id = SelectField('Member Account', coerce=int, validators=[DataRequired()])
    transaction_type = SelectField('Transaction Classification', choices=[
        ('Savings', 'Normal Savings Deposit'),
        ('Withdrawal', 'Savings Withdrawal'),
        ('Share Capital', 'Share Capital Contribution')
    ], validators=[DataRequired()])
    amount = DecimalField('Amount (KES)', places=2, validators=[
        DataRequired(),
        NumberRange(min=10, message="Minimum transaction amount is KES 10.00.")
    ])
    reference = StringField('Reference / M-Pesa Code', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Post Transaction')

class RepaymentForm(FlaskForm):
    amount = DecimalField('Repayment Amount (KES)', places=2, validators=[
        DataRequired(),
        NumberRange(min=1, message="Repayment amount must be positive.")
    ])
    reference = StringField('Reference / Receipt Number', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Record Repayment')

class LoanForm(FlaskForm):
    member_id = SelectField('Applying Member', coerce=int, validators=[DataRequired()])
    principal = DecimalField('Requested Principal (KES)', places=2, validators=[
        DataRequired(),
        NumberRange(min=500, message="Minimum loan principal is KES 500.00.")
    ])
    duration_months = SelectField('Repayment Tenure', choices=[
        ('6', '6 Months'),
        ('12', '12 Months'),
        ('24', '24 Months'),
        ('36', '36 Months')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit Loan Application')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role_id = SelectField('Assigned RBAC Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create System User')

class ActionForm(FlaskForm):
    """CSRF security token generator for destructive button submissions."""
    pass
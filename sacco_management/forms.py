from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class MemberForm(FlaskForm):
    member_no = StringField('Member No', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    national_id = StringField('National ID', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    submit = SubmitField('Register Member')

class TransactionForm(FlaskForm):
    member_id = SelectField('Select Member', coerce=int, validators=[DataRequired()])
    deposit_type = SelectField('Transaction Type', choices=[('Savings', 'Normal Savings'), ('Share Capital', 'Share Capital')], validators=[DataRequired()])
    amount = FloatField('Amount (KES)', validators=[DataRequired(), NumberRange(min=1)])
    reference = StringField('Payment Reference')
    submit = SubmitField('Submit Transaction')

class RepaymentForm(FlaskForm):
    amount = FloatField('Repayment Amount (KES)', validators=[DataRequired(), NumberRange(min=1)])
    reference = StringField('Payment Reference')
    submit = SubmitField('Submit Repayment')

class LoanForm(FlaskForm):
    member_id = SelectField('Member', coerce=int, validators=[DataRequired()])
    principal = FloatField('Requested Principal (KES)', validators=[DataRequired(), NumberRange(min=100)])
    duration_months = SelectField('Repayment Period', choices=[('6', '6 Months'), ('12', '12 Months'), ('24', '24 Months'), ('36', '36 Months')], validators=[DataRequired()])
    submit = SubmitField('Submit Application')
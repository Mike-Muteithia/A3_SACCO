from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Member
from forms import MemberForm
from utils import permission_required

members_bp = Blueprint('members', __name__)

@members_bp.route('/members', methods=['GET', 'POST'])
@login_required
@permission_required('PROFILE_READ')
def index():
    form = MemberForm()
    
    if form.validate_on_submit():
        # Check for duplicate Member Number or National ID
        if Member.query.filter((Member.member_no == form.member_no.data) | 
                               (Member.national_id == form.national_id.data)).first():
            flash('Member Number or National ID already exists.', 'danger')
        else:
            new_member = Member(
                member_no=form.member_no.data,
                full_name=form.full_name.data,
                national_id=form.national_id.data,
                phone=form.phone.data,
                email=form.email.data
            )
            db.session.add(new_member)
            db.session.commit()
            flash('Member registered successfully!', 'success')
            return redirect(url_for('members.index'))

    member_list = Member.query.order_by(Member.id.desc()).all()
    return render_template('members.html', members=member_list, form=form)

    pass

@members_bp.route('/members/<int:member_id>/delete', methods=['POST'])
@login_required
@permission_required('PROFILE_DELETE')
def delete(member_id):
    member = Member.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('Member removed securely.', 'success')
    return redirect(url_for('members.index'))
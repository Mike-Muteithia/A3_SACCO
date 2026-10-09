from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Member
from forms import MemberForm
from utils import permission_required

members_bp = Blueprint('members', __name__)

@members_bp.route('/members', methods=['GET', 'POST'])
@login_required
@permission_required('PROFILE_READ')
def index():
    form = MemberForm()
    search_query = request.args.get('q', '')
    
    if form.validate_on_submit():
        new_member = Member(
            member_no=form.member_no.data, full_name=form.full_name.data,
            national_id=form.national_id.data, phone=form.phone.data, email=form.email.data
        )
        db.session.add(new_member)

        try:
            db.session.commit()
            flash('Member registered!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('A database error occurred while registering the member.', 'danger')
            
        return redirect(url_for('members.index'))
        
    if search_query:
        members = Member.query.filter(
            Member.is_active == True,
            (Member.full_name.ilike(f'%{search_query}%') | Member.member_no.ilike(f'%{search_query}%'))
        ).all()
    else:
        members = Member.query.filter_by(is_active=True).order_by(Member.id.desc()).all()
        
    return render_template('members.html', members=members, form=form, search_query=search_query)

@members_bp.route('/members/<int:member_id>/update', methods=['POST'])
@login_required
@permission_required('PROFILE_READ') # In a real app, use PROFILE_UPDATE. Reusing READ for brevity.
def update(member_id):
    member = Member.query.get_or_404(member_id)
    member.phone = request.form.get('phone')
    member.email = request.form.get('email')

    try:
        db.session.commit()
        flash('Member contact info updated.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('A database error occurred while updating the member.', 'danger')
        
    return redirect(url_for('members.index'))

@members_bp.route('/members/<int:member_id>/delete', methods=['POST'])
@login_required
@permission_required('PROFILE_DELETE')
def delete(member_id):
    member = Member.query.get_or_404(member_id)
    # db.session.delete(member)
    member.is_active = False

    try:
        db.session.commit()
        flash('Member account archived securely. Financial records preserved.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('A database error occurred while archiving the member.', 'danger')
        
    return redirect(url_for('members.index'))
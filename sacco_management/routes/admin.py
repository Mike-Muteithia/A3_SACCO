from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from models import db, User, Role
from forms import UserForm
from utils import permission_required
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users', methods=['GET', 'POST'])
@login_required
@permission_required('USER_MANAGE') # RBAC: System Admin only
def manage_users():
    form = UserForm()
    form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
    
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password_hash=hashed_pw, role_id=form.role_id.data)
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {new_user.username} created.', 'success')
        return redirect(url_for('admin.manage_users'))
        
    users = User.query.all()
    return render_template('admin.html', users=users, form=form)

@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@permission_required('USER_MANAGE')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User account deleted.', 'success')
    return redirect(url_for('admin.manage_users'))
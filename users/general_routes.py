from flask import Blueprint, render_template, redirect, flash, g, request, url_for
from db_setup import db
from users.models import User
from users.forms import UserEditForm

from messages.models import Message

from sqlalchemy.exc import IntegrityError

user_views = Blueprint('user_routes', __name__)


##############################################################################
# General user routes:

@user_views.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.ilike(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@user_views.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)


@user_views.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@user_views.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@user_views.route('/users/<int:user_id>/likes')
def show_likes(user_id):
    """Show list of messages this user likes."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/liked_messages.html', user=user)


@user_views.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    if g.user.id == follow_id:
        flash("You Can't follow yourself Bud.", "warning")
        return redirect(f"/users/{g.user.id}")
    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@user_views.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@user_views.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = UserEditForm(obj=g.user)
    # form is valid?
    if form.validate_on_submit():
        # form has valid Pword?
        if User.authenticate(username=g.user.username, password=form.password.data):

            g.user.update_from_serial(request.form)
            db.session.add(g.user)
            try:
                db.session.commit()
                return redirect(url_for("user_routes.users_show", user_id=g.user.id))

            except IntegrityError:
                flash("Username or email already taken", 'danger')
                return render_template('/users/edit.html', form=form)
        else:
            form.password.errors.append("Password is incorrect!")
    return render_template('/users/edit.html', form=form)


@user_views.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")

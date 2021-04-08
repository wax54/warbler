from flask import Blueprint, flash, redirect, render_template, g
from db_setup import db
from messages.models import Message
from messages.forms import MessageForm

message_views = Blueprint("message_routes", __name__)


##############################################################################
# Messages routes:

@message_views.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@message_views.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@message_views.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    if msg.user_id == g.user.id:
        db.session.delete(msg)
        db.session.commit()
        return redirect(f"/users/{g.user.id}")
    else:
        flash("Delete Your Own Damn Messages!")
        return redirect(f"/users/{g.user.id}")

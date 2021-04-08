from flask import Blueprint, redirect, render_template, g


like_views = Blueprint("like_routes", __name__)

##############################################################################
# Like routes:


@like_views.route('/users/add_like/<int:msg_id>', methods=["GET", "POST"])
def like_message(msg_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(msg_id)
    #  if msg is already liked, unlike it
    if msg in g.user.likes:
        g.user.likes.remove(msg)
    #  otherwise, like it
    else:
        g.user.likes.append(msg)
    db.session.commit()
    return redirect(f'/users/{g.user.id}/likes')

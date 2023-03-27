import datetime

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.jdb import get_db, get_new_id, commit

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    username_map = {u['id']: u['username'] for u in db['users']}
    posts = []
    for p in sorted(db['posts'], key=lambda p: p['created'], reverse=True):
        post = dict(p)
        post['created'] = datetime.datetime.fromisoformat(p['created'])
        post['username'] = username_map[p['author_id']]
        posts.append(post)
    return render_template("blog/index.html", posts=posts)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    db = get_db()
    post = None
    for p in db['posts']:
        if p['id'] == id:
            post = p
            break

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db['posts'].append({
                'id': get_new_id(db['posts']),
                'author_id': g.user["id"],
                'created': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'title': title,
                'body': body
            })
            commit(db)
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            for p in db['posts']:
                if p['id'] == id:
                    p['title'] = title
                    p['body'] = body
                    break
            commit(db)
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    db = get_db()
    for i, p in enumerate(db['posts']):
        if p['id'] == id:
            del db['posts'][i]
            commit(db)
            break
    return redirect(url_for("blog.index"))

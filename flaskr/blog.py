from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    user_id = 0
    if g.user is not None:
        user_id = g.user['id']
    

    query = '''SELECT p.id, title, body, p.created, author_id, username, count(l.post_id) as likes,
    CASE WHEN ul.post_id IS NOT NULL THEN 1 ELSE 0 END AS user_liked 
    FROM post p 
    JOIN user u ON p.author_id = u.id 
    LEFT JOIN likes l on p.id = l.post_id 
    LEFT JOIN likes ul on ul.post_id = p.id AND ul.user_id = ? 
    GROUP BY p.id, p.title, p.body, p.created, p.author_id, u.username
    ORDER BY p.created DESC'''
    posts = db.execute(query, (user_id,)).fetchall()

   
    return render_template('blog/index.html', posts=posts)

'''The purpose of this JOIN operation is to combine the data from the post table and the user table so that 
you can retrieve information about both the post and the user who created it in a single query.

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view'''



'''def create():
    # function body
create = login_required(create)
'''


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


'''Both the update and delete views will need to fetch a post by id and check if the author matches the 
logged in user. To avoid duplicating code, you can write a function to get the post and call it from each view.'''


'''404 means “Not Found”, and 403 means “Forbidden”. 
(401 means “Unauthorized”, but you redirect to the login page instead of returning that status.)

WHERE clause in a query, it is applied after the FROM clause and any JOIN operations, but before the GROUP BY,
 HAVING, and ORDER BY clauses. I'''

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p'
        ' JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post



@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

'''The pattern {{ request.form['title'] or post['title'] }} is used to choose what data appears in the form. 
When the form hasn’t been submitted, the original post data appears, but if invalid form data was posted you want to display that so the user can fix the error, so request.form is used instead. request is another variable that’s automatically available in templates.'''



@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


'''The delete view doesn’t have its own template, the delete button is part of update.html and posts to the /<id>/delete URL. Since there is no template, 
it will only handle the POST method and then redirect to the index view.'''


#A detail view to show a single post. Click a post’s title to go to its page.
@bp.route('/<int:id>', methods=('GET',))
def post(id):
    post = get_db().execute('SELECT * FROM post WHERE id=?',(id,)).fetchone()
    error = None
    if not post:
        error = 'No Post Found'
        return redirect(url_for('blog.index'))
    return render_template('blog/post.html',post=post)


#a view to like
@bp.route('/<int:id>/like', methods=('POST',))
@login_required
def likeMeOrNot(id):
    if request.method == 'POST':
        db = get_db()
        count = db.execute("SELECT count(*) FROM likes WHERE post_id=? and user_id=?",(id, g.user['id'])).fetchone()[0]
        if(count is 0 ):
            db.execute(
                'INSERT INTO likes(post_id, user_id) VALUES(?,?)',(id,g.user['id'])
                )
        else: db.execute('DELETE FROM likes where post_id=? and user_id=?',(id,g.user['id']))
        db.commit()
    return redirect(url_for('blog.index'))
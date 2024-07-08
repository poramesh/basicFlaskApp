import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

import sqlite3

bp = Blueprint('auth', __name__, url_prefix='/auth') #This creates a Blueprint named 'auth'. Like the application object, the blueprint needs to know where it’s defined, so __name__ is passed as the second argument. The url_prefix will be prepended to all the URLs associated with the blueprint.


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login")) #The structure of try-except-else is as follows:

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,) #The comma after username in the tuple (username,) is necessary to indicate that it is a tuple with a single element. In Python, when creating a tuple with only one element, a trailing comma is required to distinguish it from a simple expression surrounded by parentheses.

        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear() #session is a dict that stores data across requests. 
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


'''The login_required decorator is defined as a function that takes view as its argument and returns wrapped_view, 
which performs the authentication check before calling view'''

'''@functools.wraps(view):

functools.wraps(view) is a decorator used inside login_required. It ensures that the wrapped_view function maintains 
the metadata (like __name__, __doc__, etc.) of the original view function that it wraps.
This preservation is important because it allows frameworks like Flask to correctly route requests and handle view functions, 
even when decorators are applied.'''

'''If g.user is None, indicating that no user is authenticated, the function redirects the user to the login page using 
redirect(url_for('auth.login')).
If g.user is not None, it calls the original view function (view(**kwargs)) with any provided keyword arguments (kwargs).
'''

'''The login_required function returns wrapped_view, which is now the modified version of the original view function with
 added authentication checks.'''

'''@app.route('/dashboard')
@login_required
def dashboard():
    # Only accessible if g.user is not None (authenticated user)
    return 'Welcome to the dashboard!'
'''



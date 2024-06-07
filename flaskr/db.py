import sqlite3

import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES 
        )

        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None) #pops the value db to db if it exists or else none. 
 
    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

"""
flask --app flaskr init-db
When you run a Flask command like $ flask --app flaskr init-db, you are executing a command that is part of the Flask application's CLI (Command Line Interface)
"""

def init_app(app):
    app.teardown_appcontext(close_db) # """Ensures that resources like database connections are properly cleaned up after each request."""
    app.cli.add_command(init_db_command)
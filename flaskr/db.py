import sqlite3

import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'], # app object created inside create_app() is local to that function scope. It is returned from the factory function and typically stored in a variable in your main application script (e.g., app = create_app() in run.py). Once the Flask application (app) is created, it is accessible via the current_app context variable within the request context.
            detect_types=sqlite3.PARSE_DECLTYPES  #When you set detect_types=sqlite3.PARSE_DECLTYPES, SQLite will attempt to detect and convert column values into Python types specified by the column declarations (DECLTYPE).
        )

        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None) #pops the value db to db if it exists or else none. 
 
    if db is not None:
        db.close()

'''During the request handling (some_route), g.pop('db', None) retrieves this database connection (db) from g.
After retrieving db, it is removed from g, ensuring that it won't be mistakenly reused or left open after the request completes.
'''

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
Purpose: This command is typically a custom command defined within your Flask application to initialize or reset the database. 
It is not a standard Flask command but often implemented using Flask's flask.cli extension or similar mechanisms.


"""

def init_app(app):
    app.teardown_appcontext(close_db) # """Ensures that resources like database connections are properly cleaned up after each request."""
    app.cli.add_command(init_db_command) # The app.cli.add_command() function in Flask is used to add custom CLI commands to your Flask application. These commands are typically used for administrative tasks such as database initialization, management, or other application-specific tasks that you want to execute from the command line interface.

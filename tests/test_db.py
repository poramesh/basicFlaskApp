import sqlite3

import pytest
from flaskr.db import get_db


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db() #assert db is get_db() checks that the database connection returned by get_db() is the same (i.e., the same object in memory) as the one previously obtained and stored in db.

    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute('SELECT 1')

    assert 'closed' in str(e.value)

'''This line uses pytest.raises, a context manager provided by pytest, to indicate that the code inside the with block is expected to raise 
an exception of type sqlite3.ProgrammingError.
If the specified exception is not raised within the block, the test will fail.
The exception object, if raised, will be captured in the variable e.'''

'''The SQL query 'SELECT 1' is a simple, valid SQL statement that selects the constant value 1. It doesn't interact with any tables in
 the database; it simply returns the value 1.
 
  result = db.execute('SELECT 1').fetchone()
    print(result)  # This should print (1,) or similar, depending on the database adapter'''


def test_init_db_command(runner, monkeypatch):
    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr('flaskr.db.init_db', fake_init_db)
    result = runner.invoke(args=['init-db'])
    assert 'Initialized' in result.output
    assert Recorder.called


'''It provides methods to replace or mock parts of the codebase temporarily, enabling isolated testing and preventing external dependencies from affecting test outcomes.'''
'''The runner fixture in Flask applications typically refers to an instance of flask.testing.FlaskCliRunner. This is used to invoke Flask CLI commands programmatically within tests.'''
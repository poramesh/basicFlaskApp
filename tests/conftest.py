import os
import tempfile

import pytest
from flaskr import create_app
from flaskr.db import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    }) #When you call app = create_app({'TESTING': True}), you are invoking the create_app function with a specific test_config dictionary:

    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)

    yield app

    os.close(db_fd)
    os.unlink(db_path)

'''the term app refers to the Flask application instance that is created and configured within the fixture function itself.'''

@pytest.fixture
def client(app):
    return app.test_client()

    #This fixture is typically used in test functions where interaction with the Flask application via HTTP requests is required.
    #This is crucial for testing your application’s endpoints (@app.route decorators) to ensure they return the expected responses.
'''Testing Endpoints:

You can use the client to send GET, POST, PUT, DELETE requests to different endpoints (/, /login, /api/resource) and then assert on the responses.
Example: response = client.get('/api/data'), assert response.status_code == 200.

After making a request with the client, you can assert on the response content to verify that your endpoints are returning
 the correct data or rendering the expected templates.
'''


@pytest.fixture
def runner(app):
    return app.test_cli_runner()

#This fixture is used in test functions where interaction with the Flask application via CLI commands is needed.

'''The runner fixture (app.test_cli_runner()) allows you to simulate command-line interface (CLI) commands that your Flask 
application defines using @app.cli.command.
This is useful for testing custom CLI commands that interact with your application's data or perform administrative tasks.'''


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)
    

'''Here, client is a parameter name in the constructor (__init__ method) of the AuthActions class. When an instance of AuthActions is created,
 a value for client must be provided. This client parameter refers to an object that is expected to have methods like post and get, which typically correspond to HTTP request methods.'''




'''To run the tests, use the pytest command. It will find and run all the test functions you’ve written.

'''
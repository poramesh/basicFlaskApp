
import os

from flask import Flask, app


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True) #silent=True suppresses errors that might occur if config.py does not exist. It allows the application to continue without crashing if the file is missing, which is useful when the config.py file is optional or used for environment-specific configurations.
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass #pass: This line indicates that if an OSError is caught, the program should ignore it and continue running. An OSError might occur if the directory already exists, which is typically not an error that needs to stop the program.

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    
    from . import db
    db.init_app(app)


    from . import auth
    app.register_blueprint(auth.bp)

    return app


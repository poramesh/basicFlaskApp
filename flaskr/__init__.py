
import os

from flask import Flask, app


def create_app(test_config=None):
    # create and configure the app #    # Set default configuration values
    app = Flask(__name__, instance_relative_config=True) #instance_relative_config=True The instance_relative_config parameter is used when creating the Flask app instance. Setting instance_relative_config=True allows Flask to configure the app to look for the configuration files relative to the instance folder instead of the default root folder of the application. This is useful for separating instance-specific configurations (such as different settings for development, testing, and production) from the rest of the application code.
    #The instance folder is a special directory designed to not be under version control and to store data that is specific to a particular deployment, such as configuration files, uploaded files, and the SQLite database file.
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

   # If test_config is provided, load the test configuration
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

    
    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app


from flask import Flask, render_template, request, session
from json import load
from os import environ
from os.path import abspath, dirname, join
from sqlalchemy import exc as sql_exception
from sys import dont_write_bytecode, path

# prevent python from writing *.pyc files / __pycache__ folders
dont_write_bytecode = True

path_app = dirname(abspath(__file__))
if path_app not in path:
    path.append(path_app)

from database import db, create_database
from models import *

def configure_database(app):
    create_database()
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()
    db.init_app(app)

def configure_socket(app):
    async_mode, thread = None, None
    socketio = SocketIO(app, async_mode=async_mode)
    thread_lock = Lock()
    return socketio
    
def import_graph():
    pass

def create_app(config='config'):
    app = Flask(__name__)
    app.config.from_object('config')
    configure_database(app)
    import_cities()
    return app

app = create_app()

## Views

@app.route('/', methods = ['GET', 'POST'])
def algorithm():
    session['best'] = float('inf')
    view = request.form['view'] if 'view' in request.form else '2D'
    return render_template(
        'index.html',
        minimum_population = 500000,
        view = view,
        cities = {
            city.id: {
                property: getattr(city, property)
                for property in City.properties
                }
            for city in City.query.all()
            },
        )

if __name__ == '__main__':
    socketio.run(
        app, 
        port = int(environ.get('PORT', 5100))
        )

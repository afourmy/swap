from collections import OrderedDict
from flask import Flask, jsonify, render_template, request, session
from json import dumps
from os.path import abspath, dirname, join
from sys import dont_write_bytecode, path
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError

dont_write_bytecode = True
path_app = dirname(abspath(__file__))
if path_app not in path:
    path.append(path_app)

from solver import Solver
from database import db, create_database
from models import *


def configure_database(app):
    create_database()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()
    db.init_app(app)


def configure_socket(app):
    async_mode = None
    socketio = SocketIO(app, async_mode=async_mode)
    thread_lock = Lock()
    return socketio


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'key'
    configure_database(app)
    solver = Solver()
    return app, solver


app, solver = create_app()


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'file' in request.files:
        filename = request.files['file'].filename
        if allowed_file(filename, {'xls', 'xlsx'}):
            filename = secure_filename(filename)
            filepath = join(path_app, 'data', filename)
            request.files['file'].save(filepath)
            sheet = open_workbook(filepath).sheet_by_index(0)
            properties = sheet.row_values(0)
            db.session.query(City).delete()
            for row_index in range(1, sheet.nrows):
                city_dict = dict(zip(properties, sheet.row_values(row_index)))
                city = City(**city_dict)
                db.session.add(city)
            db.session.commit()
            tsp.update_data()
    session['best'] = float('inf')
    session['crossover'], session['mutation'] = 'OC', 'Swap'
    view = request.form['view'] if 'view' in request.form else '2D'
    cities = {
        city.id: OrderedDict([
            (property, getattr(city, property))
            for property in City.properties
            ])
        for city in City.query.all()
        }
    return render_template(
        'index.html',
        view=view,
        cities=cities
        )


@app.route('/<algorithm>', methods=['POST'])
def algorithm(algorithm):
    session['best'] = float('inf')
    return jsonify(*getattr(tsp, algorithm)())


if __name__ == '__main__':
    app.run(
        host = '0.0.0.0',
        port = 5000,
        threaded = True
        )

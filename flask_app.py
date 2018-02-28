from collections import OrderedDict
from flask import Flask, jsonify, render_template
from os.path import abspath, dirname
from sys import dont_write_bytecode, path
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


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'key'
    configure_database(app)
    solver = Solver()
    return app, solver


app, solver = create_app()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if allowed_file(secure_filename(file.filename), {'xls', 'xlsx'}):  
            book = open_workbook(file_contents=file.read())
            for obj_type, cls in object_class.items():
                try:
                    sheet = book.sheet_by_name(obj_type)
                # if the sheet cannot be found, there's nothing to import
                except XLRDError:
                    continue
                properties = sheet.row_values(0)
                for row_index in range(1, sheet.nrows):
                    kwargs = dict(zip(properties, sheet.row_values(row_index)))
                    kwargs['type'] = obj_type
                    object_factory(db, **kwargs)
                db.session.commit()
    return render_template(
        'index.html',
        cities = {}
        )


@app.route('/<algorithm>', methods=['POST'])
def algorithm(algorithm):
    return jsonify(*getattr(tsp, algorithm)())


if __name__ == '__main__':
    app.run(
        host = '0.0.0.0',
        port = 5000,
        threaded = True,
        debug = True
        )

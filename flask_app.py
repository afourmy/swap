from flask import Flask, render_template, request, session
from json import load
from os import environ
from os.path import abspath, dirname, join
from sqlalchemy import exc as sql_exception
from sys import dont_write_bytecode, path
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError

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
    
def import_graph():
    pass

def create_app(config='config'):
    app = Flask(__name__)
    app.config.from_object('config')
    configure_database(app)
    return app

app = create_app()

## Views

def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension

@app.route('/object_creation', methods=['GET', 'POST'])
def create_objects():
    add_objects_form = AddObjects(request.form)
    if 'add_objects' in request.form:
        filename = request.files['file'].filename
        if 'file' in request.files and allowed_file(filename, {'xls', 'xlsx'}):  
            filename = secure_filename(filename)
            filepath = join(current_app.config['UPLOAD_FOLDER'], filename)
            request.files['file'].save(filepath)
            book = open_workbook(filepath)
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
        else:
            flash('no file submitted')
    return render_template(
        'index.html',
        add_objects_form = add_objects_form
        )

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
    app.run(
        host = '0.0.0.0',
        port = int(environ.get('PORT', 5100)),
        threaded = True
        )

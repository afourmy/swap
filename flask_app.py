from collections import defaultdict, OrderedDict
from flask import Flask, jsonify, render_template, request, session
from os.path import abspath, dirname
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
from models import Fiber, object_class, object_factory, Traffic


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


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


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
    objects = {
        obj_type: {
            obj: OrderedDict([
                (property, getattr(obj, property))
                for property in cls.properties
            ])
            for obj in cls.query.all()
        }
        for obj_type, cls in object_class.items()
    }
    return render_template(
        'index.html',
        objects=objects
    )


@app.route('/graph_transformation', methods=['POST'])
def graph_transformation():
    session['transformed_graph'], vis_graph = solver.graph_transformation()
    return jsonify(vis_graph)


@app.route('/graph_coloring/<algorithm>', methods=['POST'])
def graph_coloring(algorithm):
    
    results = getattr(solver, algorithm)(session['transformed_graph'])
    colors_per_fiber = defaultdict(list)
    for traffic in Traffic.query.all():
        for fiber in Fiber.query.all():
            if fiber.name in traffic.path:
                colors_per_fiber[fiber.name].append(results['colors'][traffic.name])
    results['fiber_colors'] = colors_per_fiber
    return jsonify(results)


@app.route('/<algorithm>', methods=['POST'])
def algorithm(algorithm):
    return jsonify(getattr(solver, algorithm)())





@app.route('/path_<traffic_link>', methods=['POST'])
def get_path(traffic_link):
    traffic = db.session.query(Traffic).filter_by(name=traffic_link).first()
    return jsonify(traffic.path)


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True,
        debug=True
    )

from collections import defaultdict, OrderedDict
from flask import Blueprint, jsonify, render_template, request, session
from werkzeug.utils import secure_filename
from xlrd import open_workbook

from swap import db
from swap.models import (
    Fiber,
    Link,
    Node,
    Object,
    object_class,
    object_factory,
    Traffic
)
from swap.solver import Solver

swap, solver = Blueprint('swap', __name__), Solver()


def allowed_file(name, allowed_extensions):
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


@swap.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        for model in (Fiber, Traffic, Link, Node, Object):
            model.query.delete()
            db.session.commit()
        file = request.files['file']
        if allowed_file(secure_filename(file.filename), {'xls', 'xlsx'}):
            book = open_workbook(file_contents=file.read())
            for obj_type, cls in object_class.items():
                sheet = book.sheet_by_name(obj_type)
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
        for obj_type, cls in (('Node', Node), ('Link', Link))
    }
    return render_template('index.html', objects=objects)


@swap.route('/routing', methods=['POST'])
def routing():
    session['paths'] = solver.shortest_path()
    return jsonify({})


@swap.route('/graph_transformation', methods=['POST'])
def graph_transformation():
    graph, vis_graph = solver.graph_transformation(session['paths'])
    session['transformed_graph'] = graph
    return jsonify(vis_graph)


@swap.route('/wavelength_assignment/<algorithm>', methods=['POST'])
def graph_coloring(algorithm):
    results = getattr(solver, algorithm)(session['transformed_graph'])
    colors_per_fiber, coords = defaultdict(list), {}
    for traffic in Traffic.query.all():
        for fiber in Fiber.query.all():
            if fiber.name in session['paths'][traffic.name]:
                colors_per_fiber[fiber.name].append(results['colors'][traffic.name])
                coords[fiber.name] = (
                    (fiber.source.longitude, fiber.source.latitude),
                    (fiber.destination.longitude, fiber.destination.latitude)
                )
    results['fiber_colors'], results['coords'] = colors_per_fiber, coords
    return jsonify(results)


@swap.route('/path_<traffic_link>', methods=['POST'])
def get_path(traffic_link):
    return jsonify(session['paths'][traffic_link])

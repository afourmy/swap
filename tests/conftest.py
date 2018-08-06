from os.path import abspath, dirname, join, pardir
from pytest import fixture

from swap import create_app, db

path = abspath(join(dirname(abspath(__file__)), pardir))
path_examples = join(path, 'examples')


@fixture
def client():
    app = create_app()
    app_context = app.app_context()
    app_context.push()
    db.session.close()
    db.drop_all()
    yield app.test_client()

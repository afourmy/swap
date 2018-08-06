from tests.conftest import path_examples
from swap.models import Node, Fiber, Traffic
from os.path import join


def create_from_file(client, file):
    with open(join(path_examples, file), 'rb') as f:
        data = dict(file=f)
        client.post('/', data=data)


def swap_algorithm_test(client):
    client.post('/routing')
    for traffic in Traffic.query.all():
        client.post('/path_' + traffic.name)
    client.post('/routing')
    client.post('/graph_transformation')
    client.post('/wavelength_assignment/largest_degree_first')
    client.post('/wavelength_assignment/linear_programming')
    client.get('/').status_code == 200


def count_objects(nodes, fibers, traffics):
    assert len(Node.query.all()) == nodes
    assert len(Fiber.query.all()) == fibers
    assert len(Traffic.query.all()) == traffics


def test_simple(client):
    assert client.get('/').status_code == 200
    create_from_file(client, 'simple.xls')
    count_objects(5, 4, 5)
    swap_algorithm_test(client)


def test_europe(client):
    assert client.get('/').status_code == 200
    create_from_file(client, 'europe.xls')
    count_objects(33, 48, 7)
    swap_algorithm_test(client)


def test_usa(client):
    assert client.get('/').status_code == 200
    create_from_file(client, 'usa.xls')
    count_objects(27, 28, 11)
    swap_algorithm_test(client)


def test_data_overwrite(client):
    create_from_file(client, 'usa.xls')
    create_from_file(client, 'europe.xls')
    count_objects(33, 48, 7)
    create_from_file(client, 'usa.xls')
    count_objects(27, 28, 11)

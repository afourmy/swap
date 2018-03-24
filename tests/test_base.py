from conftest import path_examples
from models import Node, Fiber, Traffic
from os.path import join


def create_from_file(client, file):
    with open(join(path_examples, file), 'rb') as f:
        data = dict(file=f)
        client.post('/', data=data)


def test_authentication(client):
    assert client.get('/').status_code == 200
    create_from_file(client, 'europe.xls')
    assert len(Node.query.all()) == 33
    assert len(Fiber.query.all()) == 48
    assert len(Traffic.query.all()) == 7
    client.post('/routing')
    for traffic in Traffic.query.all():
        client.post('/path_' + traffic.name)
    client.post('/routing')
    client.post('/graph_transformation')
    client.post('/wavelength_assignment/largest_degree_first')
    client.post('/wavelength_assignment/linear_programming')
    client.get('/').status_code == 200

from collections import OrderedDict
from database import Base
from math import asin, cos, radians, sin, sqrt
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import backref, relationship


class Object(Base):

    __tablename__ = 'Object'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)


class Node(Object):

    __tablename__ = 'Node'

    properties = (
        'name',
        'longitude',
        'latitude'
    )

    id = Column(Integer, ForeignKey('Object.id'), primary_key=True)
    longitude = Column(Float)
    latitude = Column(Float)

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)

    def adjacencies(self, type):
        adj = [(x.source, x) for x in self.higher_edges]
        adj.extend([(x.destination, x) for x in self.lower_edges])
        return filter(lambda a: a[1].subtype == type, adj)


class Link(Object):

    __tablename__ = 'Link'

    __mapper_args__ = {
        'polymorphic_identity': 'Link',
    }

    properties = (
        'name',
        'subtype',
        'source',
        'destination',
        'distance',
    )

    id = Column(Integer, ForeignKey('Object.id'), primary_key=True)
    subtype = Column(String)
    distance = Column(Integer)

    source_id = Column(
        Integer,
        ForeignKey('Node.id')
    )

    destination_id = Column(
        Integer,
        ForeignKey('Node.id')
    )

    source = relationship(
        Node,
        primaryjoin=source_id == Node.id,
        backref=backref('lower_edges', cascade="all, delete-orphan")
    )

    destination = relationship(
        Node,
        primaryjoin=destination_id == Node.id,
        backref=backref('higher_edges', cascade="all, delete-orphan")
    )

    def __init__(self, **kwargs):
        super(Link, self).__init__(**kwargs)
        self.distance = 1


class Fiber(Link):

    __tablename__ = 'Fiber'

    __mapper_args__ = {
        'polymorphic_identity': 'Fiber',
    }

    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)

    def __init__(self, **kwargs):
        super(Fiber, self).__init__(**kwargs)
        self.subtype = 'fiber'
        self.compute_distance()

    def hav(self, angle):
        return sin(angle / 2)**2

    def compute_distance(self):
        coords = (
            self.source.latitude, self.source.longitude,
            self.destination.latitude, self.destination.longitude
        )
        # we convert from decimal degree to radians
        lat_cityA, lon_cityA, lat_cityB, lon_cityB = map(radians, coords)
        delta_lon = lon_cityB - lon_cityA
        delta_lat = lat_cityB - lat_cityA
        a = self.hav(delta_lat) + cos(lat_cityA) * cos(lat_cityB) * self.hav(delta_lon)
        c = 2 * asin(sqrt(a))
        # approximate radius of the Earth: 6371 km
        self.distance = int(c * 6371)


class Traffic(Link):

    __tablename__ = 'Traffic'

    __mapper_args__ = {
        'polymorphic_identity': 'Traffic',
    }

    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)

    def __init__(self, **kwargs):
        super(Traffic, self).__init__(**kwargs)
        self.subtype = 'traffic'


object_class = OrderedDict([
    ('Node', Node),
    ('Fiber', Fiber),
    ('Traffic', Traffic)
])


def get_obj(db, model, **kwargs):
    return db.session.query(model).filter_by(**kwargs).first()


def object_factory(db, **kwargs):
    obj_type = kwargs['type']
    if obj_type == 'Node':
        obj = object_class[obj_type](**kwargs)
    else:
        source = get_obj(db, Node, name=kwargs.pop('source'))
        destination = get_obj(db, Node, name=kwargs.pop('destination'))
        obj = object_class[obj_type](
            source_id=source.id,
            destination_id=destination.id,
            source=source,
            destination=destination,
            **kwargs
        )
    db.session.add(obj)
    db.session.commit()

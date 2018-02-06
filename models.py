from collections import OrderedDict
from database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import backref, relationship

class Object(Base):
    
    # __abstract__ = True
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
    
    id = Column(Integer, ForeignKey('Object.id'), primary_key=True)
    longitude = Column(Float)
    latitude = Column(Float)
    
    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)

class Link(Object):
    
    __tablename__ = 'Link'

    id = Column(Integer, ForeignKey('Object.id'), primary_key=True)
    
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
        primaryjoin = source_id == Node.id,
        backref = backref('source', cascade="all, delete-orphan")
        )

    destination = relationship(
        Node,
        primaryjoin = destination_id == Node.id,
        backref = backref('destination', cascade="all, delete-orphan")
        )
        
    properties = OrderedDict([
        ('source', 'Source'),
        ('destination', 'Destination')
        ])

        
    def __init__(self, **kwargs):
        super(Link, self).__init__(**kwargs)

def object_factory(db, **kwargs):
    obj_type = kwargs['type']
    cls = Node if obj_type in node_class else Link
    obj = get_obj(db, cls, name=kwargs['name'])
    if obj:
        for property, value in kwargs.items():
            if property in obj.__dict__:
                setattr(obj, property, value)
    elif obj_type in link_class:
        source = get_obj(db, Node, name=kwargs.pop('source'))
        destination = get_obj(db, Node, name=kwargs.pop('destination'))
        obj = link_class[obj_type](
            source_id = source.id, 
            destination_id = destination.id, 
            source = source, 
            destination = destination,
            **kwargs
            )
    else:
        obj = object_class[obj_type](**kwargs)
    db.session.add(obj)
    db.session.commit()
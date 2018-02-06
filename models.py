from database import Base
from sqlalchemy import Column, Integer, String, Float

class Object(Base):
    
    __tablename__ = 'Object'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)

    
    __mapper_args__ = {
        'polymorphic_identity':'Object',
        'polymorphic_on': type
    }
    
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
    
    __mapper_args__ = {
        'polymorphic_identity':'Node',
    }
    
    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)

class Link(Object):
    
    __tablename__ = 'Link'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Link',
    }

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

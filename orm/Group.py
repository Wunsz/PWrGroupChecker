from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Time, DateTime

Base = declarative_base()

class Group(Base):
    __tablename__ = 'groups'

    id_group = Column(String(16), primary_key=True)
    id_course = Column(String(16), ForeignKey("Course.id_course"), nullable=False)
    capacity = Column(Integer)
    assigned = Column(Integer)
    building = Column(String(16), nullable=False)
    room = Column(String(16), nullable=False)
    day = Column(Integer(1))
    start = Column(Time)
    end = Column(Time)
    lecturer = Column(String(255))
    updated = Column(DateTime, nullable=False)
    last_change = Column(DateTime)

    def __init__(self, id_course, name, type):
        self.id_course = id_course
        self.name = name
        self.type = type

    def __repr__(self):
        return "<Group(%s, %s, %s/%s)>" % (
            self.id_group, self.id_course, self.assigned, self.capacity)
# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Time, DateTime

Base = declarative_base()

class Group(Base):
    __tablename__ = 'groups'

    id_group = Column(String(16), primary_key=True)
    id_course = Column(String(16), nullable=False)
    capacity = Column(Integer)
    assigned = Column(Integer)
    building = Column(String(16), nullable=False)
    room = Column(String(16), nullable=False)
    day = Column(Integer())
    start = Column(Time)
    end = Column(Time)
    lecturer = Column(String(255))
    updated = Column(DateTime, nullable=False)
    last_change = Column(DateTime)

    def __init__(self, id_group, id_course, assigned, capacity):
        self.id_group = id_group
        self.id_course = id_course
        self.assigned = assigned
        self.capacity = capacity

    def __repr__(self):
        return "<Group(%s, %s, %s/%s)>" % (
            self.id_group, self.id_course, self.assigned, self.capacity)
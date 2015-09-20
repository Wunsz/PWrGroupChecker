# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey

Base = declarative_base()

class Course(Base):
    __tablename__ = 'courses'

    id_course = Column(String(16), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(2), nullable=False)

    def __init__(self, id_course, name, type):
        self.id_course = id_course
        self.name = name
        self.type = type

    def __repr__(self):
        return "<Course(%s, %s, %s)>" % (
            self.id_course, self.name, self.type)
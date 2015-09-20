# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class CourseType(Base):
    __tablename__ = 'courses_types'

    id_course_type = Column(String(2), primary_key=True)
    type = Column(String(45), nullable=False)
    polish = Column(String(45), nullable=False)

    def __init__(self, id_course_type, type, polish):
        self.id_course_type = id_course_type
        self.type = type
        self.polish = polish

    def __repr__(self):
        return "<CourseType(%s, %s, %s)>" % (
            self.id_course_type, self.type, self.polish)
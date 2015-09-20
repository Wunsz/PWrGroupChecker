from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Time, DateTime

Base = declarative_base()

class GroupLog(Base):
    __tablename__ = 'groups_logs'

    id_group = Column(String(16), primary_key=True)
    id_course = Column(String(16), ForeignKey("Group.id_group"), nullable=False)
    assigned = Column(Integer)
    check_time = Column(DateTime, nullable=False)

    def __init__(self, id_group, id_course, assigned):
        self.id_group = id_group
        self.id_course = id_course
        self.assigned = assigned
        self.check_time = DateTime()

    def __repr__(self):
        return "<GroupLog(%s, %s, %s/%s)>" % (
            self.id_group, self.id_course, self.assigned, self.check_time)
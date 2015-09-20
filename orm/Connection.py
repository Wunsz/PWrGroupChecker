# -*- coding: utf-8 -*-
import configparser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

__author__ = 'bjablonski'


class Connection:
    @staticmethod
    def session():
        parser = configparser.ConfigParser()
        parser.read("settings.ini")

        connection_string = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8' % (
            parser.get("Database", "user"),
            parser.get("Database", "password"),
            parser.get("Database", "host"),
            parser.get("Database", "port"),
            parser.get("Database", "database"),
        )

        # echo = True, ativa debug
        engine = create_engine(connection_string, echo=True, encoding='utf8')
        Session = sessionmaker(bind=engine)

        return Session()

# -*- coding: utf-8 -*-
import configparser

class DB:
    name = None

    @staticmethod
    def get_name():
        if DB.name is None:
            parser = configparser.ConfigParser()
            parser.read("settings.ini")
            DB.name = parser.get("Database", "database")

        return DB.name

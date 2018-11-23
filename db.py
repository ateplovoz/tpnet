# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 tw=79
"""
======
db.py
database control module

this module is a part of TPNet — Transport Net simulation model
Copyright © 2018 Vadim Pribylov

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.    If not, see <https://www.gnu.org/licenses/>.
======

Description
------
This module provides access to database file and function to log entries into
according tables

Requires
------
sqlite3 (standard)
datetime (standard)
os (standard)
glob (standard)

Classes
------

Variables
-----
"""
# TODO: finish module docstring
# TODO: make configuration possible

import sqlite3
import datetime
import os
import glob

current_db = None
dbconfig = {
    'enable': True,
    'renew': True,
}


class CurrentDb():
    """
    Connect to current database and return cursor to this database
    """
    def __init__(self):
        """This class provides access to the database"""
        self.current_db = current_db

    def __enter__(self):
        """Connect to database and return cursor"""
        self.con = sqlite3.connect(current_db)
        return DatabaseProxy(self.con)

    def __exit__(self, type, value, traceback):
        """Close database connection when done"""
        self.con.commit()
        self.con.close()


class DatabaseProxy():
    """Class for convenient logging and other functions"""

    def __init__(self, conn):
        """
        Initialize database proxy with connection and cursor pointing
        to the current sqlite database in use
        """
        self.conn = conn
        self.cursor = conn.cursor()

    def log(self, msg, obj_type='sys', obj_id=0):
        """
        Put an entry into SQLite log

        Arguments
        ------
        obj_type: str, max 3 chars
            type of the object
        obj_id: int
            unique id number of object
        msg: str
            message to put into log
        """

        if len(obj_type) > 3:
            raise ValueError('`obj_type` must be exactly 3 symbols')
        self.cursor.execute(
            'INSERT INTO log (object_type,object_id,message)'
            'VALUES (?,?,?);',
            (obj_type, obj_id, msg)
        )


def new_db():
    """
    Create new database file according to schema.sql and set `current_db` to
    new filename
    """
    global current_db
    current = datetime.datetime.now()
    filename = os.path.join(
        os.getcwd(), 'db',
        '{0:04}{1:02}{2:02}_{3:02}{4:02}.db'.format(
            current.year, current.month, current.day,
            current.hour, current.minute
        )
    )
    # create new database file
    open(filename, 'w+')
    current_db = filename
    schema = open('schema.sql', 'r').read()
    with CurrentDb() as db:
        db.cursor.execute(schema)


def clean_db():
    """
    Removes all database files
    """

    i = 0
    for dbfile in glob.glob(os.path.join(os.getcwd(), 'db', '*.db')):
        i += 1
        os.remove(dbfile)
    print('{0} files deleted'.format(i))

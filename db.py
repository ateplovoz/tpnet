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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
        """Just get the current database filename"""
        self.current_db = current_db

    def __enter__(self):
        """Connect to database and return cursor"""
        self.con = sqlite3.connect(current_db)
        return self.con.cursor()

    def __exit__(self, type, value, traceback):
        """Close database connection when done"""
        self.con.commit()
        self.con.close()


def new_db():
    """
    Create new database file according to schema.sql and set `current_db` to
    new filename
    """
    global current_db
    current = datetime.datetime.now()
    filename = os.path.join(
        os.getcwd(), 'db',
        '{0}{1}{2}_{3}{4}.sqlite3_db'.format(
            current.year, current.month, current.day,
            current.hour, current.minute
        )
    )
    # create new database file
    open(filename, 'w+')
    current_db = filename
    schema = open('schema.sql', 'r').read()
    with CurrentDb() as db:
        db.execute(schema)


def clean_db():
    """
    Removes all database files
    """

    i = 0
    for dbfile in glob.glob(os.path.join(os.getcwd(), 'db', '*.sqlite3_db')):
        i += 1
        os.remove(dbfile)
    print('{0} files deleted'.format(i))


def log(msg, obj_type='sys', obj_id=0):
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
    with CurrentDb() as db:
        db.execute(
            'INSERT INTO log (object_type,object_id,message) VALUES (?,?,?);',
            (obj_type, obj_id, msg)
        )

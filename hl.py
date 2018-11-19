# -*- coding: utf-8 -*-
"""
======
hl.py
high level control module

TPNet — Transport Net simulation model
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
this module provides automated functions for transport net creation and
high-level control.

TODO: write more in description

Modules
------
TODO: describe modules (db, tpnet)

Functions
------
TODO: describe functions

Constants
------
TODO: describe constants if any

Variables
------
evalt: int (default: 1000)
    total number of steps in arbitrary units.
deltat: float (default: 1)
    step value in arbitrary units.
units: str (default 's')
    step units. Optional. Recommended to set this to time units: seconds,
    minutes, hours, days or other.
"""

import json
import tpnet
from collections import deque

config = {
    'evalt': 1000,
    'deltat': 1,
    'units': 's',
}


def net_from_json(netfile):
    """
    Creates Net from JSON file

    Arguments
    -------
    netfile: str
        JSON file that contains transport net description. For example see
        example_net.json file.
    """
    netdict = json.loads(open(netfile).read())
    vertnames = []
    insides = []
    carsontrack = []
    edges = []
    for vert in netdict:
        vertnames.append(vert['name'])
        insides.append(deque(vert['inside']))
        carsontrack.append(deque(vert['ontrack']))
        for edge in vert['edges']:
            edges.append((vert['name'], edge['t']))
    return tpnet.Net(
        len(vertnames), vertnames, edges,
        inside=insides, ontrack=carsontrack
    )

"""
Module of transport net functions
======

Requires:
    random
    numpy
    graph_tool.all

Classes:
    Net - transport net class

------
a: Vadim Pribylov, 2018
JIHT RAS / PFUR
"""

import random
import numpy as np
from graph_tool.all import *


class Net:
    """
    Transport network class

    Variables:
    ------
    g: graph_tool.Graph
        `Graph` object that contains all information about network
    vname: graph_tool.PropertyMap (type: string)
        vertex names. Might be absent if no names were
        provided to constructor
    vload: graph_tool.PropertyMap (type: object)
        current load of each vertex.
    vloadargs: graph_tool.PropertyMap (type: vector<float>)
        attributes of function for periodic load change
    """

    def __init__(self, size, names=None, edges=None, **kwargs):
        """
        Initialize Net

        Args
        ------
        size: int
            number of vertices in graph
        names: iter(str)
            list of vertex names, optional
        edges: iter(tuple(str, str))
            list of edges between vertices

        Kwargs
        ------
        max_random_edges: int
            amount of random edges to generate. Default: `size`*2
        load: iter(`Passenger`)
            iterator of starting load for vertices. Must contain Passenger
            class objects. Default: []
        loadargs: iter(tuple(float, float))
            iterator of (frequency, offset) of periodic load function, must be
            size of `size`. This influences on how many Passenger-class objects
            to spawn on next iteration. Default: None
        """

        # TODO: random edges in graph

        self.g = Graph(directed=False)
        self.g.add_vertex(size)

        if names:
            self.vname = self.g.new_vertex_property('string')
            for item, name in zip(self.g.vertices(), names):
                self.vname[item] = name
            self.vnamelup = {
                key: value
                for (key, value) in zip(self.g.get_vertices(), names)
            }
        if edges:
            edges_indexed = [
                (self.vnamelup[name1], self.vnamelup[name2])
                for name1, name2 in edges
            ]
        else:
            random_edges = [
                random.sample(range(size), 2) for _ in range(size*2)
            ]
            edges_indexed = [
                (first, second)
                for first, second in random_edges
            ]
        self.g.add_edge_list(edges_indexed)

        self.vload = self.g.new_vertex_property('object')
        if load in kwargs:
            for v, l in zip(self.g.vertices(), kwargs['load']):
                self.vload[v] = l
        else:
            for v in self.g.vertices():
                self.vload[v] = []

        if loadargs in kwargs:
            self.vloadargs = self.g.new_vertex_property('vector<float>')
            for v, la in zip(self.g.vertices(), kwargs['loadargs']):
                self.vloadargs[v] = la


class Car:
    """
    Car class. Cars transfer passengers. Cars travel inside Net with
    predetermined route

    Variables
    ------
    route: iter(str) or iter(int)
        route to follow. If `namelup` is True then `cur` is vertex name.
        Otherwise it is vertex index.

    cur: str or int
        current vertex position. If `namelup` is True then `cur` is vertex
        name.  Otherwise it is vertex index.
    size: int
        maximum capacity of passengers
    inside: int
        current amount of passengers
    namelup: bool
        whether to work with `Net` vertex names. If True then looks up vertex
        names, otherwise looks for vertex index
    """

    def __init__(self, route, size=20, **kwargs):
        """
        Initialize Car.

        Args
        ------
        route: iter(str) or iter(int)
            route to follow, must contain either vertex names or vertex indices
        size: int
            car passenger capacity. Default: 20

        Kwargs
        ------
        inside: int
            starting amount of passengers. Default: 0
        """

        self.size = size
        if amount in kwargs:
            self.inside = kwargs['amount']
        else:
            self.inside = 0

        # check if route contains names
        if isinstance(route[0], str):
            # now check if it is actually integers in string form
            try:
                self.route = [int(item) for item in route]
            except ValueError:
                self.route = route
                self.namelup = True
        elif isinstance(route[0], int):
            self.route = route
        else:
            raise ValueError(
                'route expected to be iter(str) or iter(int). '
                'got {}'.format.type(route)
            )


class Passenger:
    """
    Passsenger class. Passengers travel via Cars with predetermined route.

    Variables
    -----
    route: iter(str) or iter(int)
        route to follow. If `namelup` is True then `cur` is vertex name.
        Otherwise it is vertex index.

    cur: str or int
        current vertex position. If `namelup` is True then `cur` is vertex
        name.  Otherwise it is vertex index.

    namelup: bool
        whether to work with `Net` vertex names. If True then looks up vertex
        names, otherwise looks for vertex index.
    """

    def __init__(self, route, **kwargs):
        """
        Initialize Passenger

        Args
        ------
        route: iter(str) or iter(int)
            route to follow, must contain either vertex names or vertex
            indices.

        Kwargs
        ------
        cur: str or int
            current vertex position. Avoid using this argument unless you know
            what you are doing, because this may lead to stuck passengers.
            `cur` must be same type as `route` to avoid improper `namelup`
            assignment. Default: `route[0]`
        """

        # check if route contains names
        if isinstance(route[0], str):
            # now check if it is actually integers in string form
            try:
                self.route = [int(item) for item in route]
            except ValueError:
                self.route = route
                self.namelup = True
        elif isinstance(route[0], int):
            self.route = route
        else:
            raise ValueError(
                'route expected to be iter(str) or iter(int). '
                'got {}'.format.type(route)
            )

        if cur in kwargs:
            self.cur = kwargs['cur']
        else:
            self.cur = route[0]

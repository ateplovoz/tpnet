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


class Net(self):
    """
    Transport network class

    TODO: add more text
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

        KWArgs
        ------
        max_random_edges: int
            amount of random edges to generate. Default: `size`*2
        load: iter(float)
            iterator of starting load for vertices. Default: 0
        loadargs: iter(tuple(float, float))
            iterator of (frequency, offset) of periodic load function, must be
            size of `size`. Default: None

        Returns: tuple(graph, net)
        ------
        graph: graph_tool.Graph
            resulting graph
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

        self.vload = self.g.new_vertex_property('short')
        if load in kwargs:
            for v, l in zip(self.g.vertices(), kwargs['load']):
                self.vload[v] = l
        else:
            for v in self.g.vertices():
                self.vload[v] = 0

        if loadargs in kwargs:
            self.vloadargs = self.g.new_vertex_property('vector<float>')
            for v, la in zip(self.g.vertices(), kwargs['loadargs']):
                self.vloadargs[v] = la

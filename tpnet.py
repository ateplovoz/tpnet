"""
Module of transport net functions
======

Requires:
    random
    numpy
    graph_tool.all

Functions:
    init - initialize transport net

------
a: Vadim Pribylov, 2018
JIHT RAS / PFUR
"""

import random
import numpy as np
from graph_tool.all import *


def init(size, names=None, edges=None, **kwargs):
    """
    Initialize graph

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
        iterator of (frequency, offset) of periodic load function, must be size
        of `size`. Default: None

    Returns: tuple(graph, net)
    ------
    graph: graph_tool.Graph
        resulting graph
    """

    # TODO: random edges in graph

    g = Graph(directed=False)
    g.add_vertex(size)

    if names:
        vname = g.new_vertex_property('string')
        for item, name in zip(g.vertices(), names):
            vname[item] = name
        vnamelup = {
            key: value for (key, value) in zip(g.get_vertices(), names)
        }
    if edges:
        edges_indexed = [
            (vnamelup[name1], vnamelup[name2]) for name1, name2 in edges
        ]
    else:
        random_edges = [random.sample(range(size), 2) for _ in range(size*2)]
        edges_indexed = [
            (first, second)
            for first, second in random_edges
        ]
    g.add_edge_list(edges_indexed)

    vload = g.new_vertex_property('short')
    if load in kwargs:
        for v, l in zip(g.vertices(), kwargs['load']):
            vload[v] = l
    else:
        for v in g.vertices():
            vload[v] = 0

    if loadargs in kwargs:
        vloadargs = g.new_vertex_property('vector<float>')
        for v, la in zip(g.vertices(), kwargs['loadargs']):
            vloadargs[v] = la

    net = {'g': g}
    if vname:
        net['vname'] = vname
        net['vnamelup'] = vnamelup
    net['vload'] = vload
    if vloadargs:
        net['vloadargs'] = vloadargs

    return net

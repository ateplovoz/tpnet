"""
Module of transport net functions and classes
======

Requires:
    random (standart)
    collections (standart)
    numpy
    graph_tool

Classes:
    Net - class for graph network and related functions
    Car - class that navigates Net and transfers Passenger
    Passenger - class that represents a passenger

------
a: Vadim Pribylov, 2018
JIHT RAS / PFUR
"""

import random
from collections import deque
import numpy as np
import graph_tool as gt


class Net:
    """
    Transport network class

    Variables
    ------
    g: graph_tool.Graph
        `Graph` object that contains all information about network
    vname: graph_tool.PropertyMap (type: string)
        vertex names. Might be absent if no names were provided to constructor
    namelup: dict
        dictionary that provides index lookup by name
    vload: graph_tool.PropertyMap (type: object)
        current load of each vertex.
    vloadargs: graph_tool.PropertyMap (type: vector<float>)
        attributes of function for periodic load change
    vinside: graph_tool.PropertyMap (type: object)
        deque of `Passenger` objects inside of each `g` vertex
    vontrack: graph_tool.PropertyMap (type: object)
        deque of `Car` objects inside of each `g` vertex

    Methods
    ------
    get_route:
        returns deque of vertex indices that form route from one vertex to
        another
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
        weight: iter(float)
            weight property of `g` edges. Must be size of `edges` or `size*2`
            if `edges` is None. Default: 1
        inside: iter(iter(`Passenger`))
            starting passengers. Must be an iterable that contains deques with
            `Passenger` objects for each vertex. Passengers are assigned
            according to vertex index. Default: collections.deque([])
        ontrack: iter(iter(`Car`))
            starting cars. Must be an iterable that contains deques with `Car`
            objects for each vertex. Cars are assigned according to vertex
            index. Default: collections.deque([])
        """

        # TODO: random edges in graph

        self.g = gt.Graph(directed=False)
        self.g.add_vertex(size)

        if names:
            self.vname = self.g.new_vertex_property('string')
            for item, name in zip(self.g.vertices(), names):
                self.vname[item] = name
            self.namelup = {
                key: value
                for (key, value) in zip(names, self.g.get_vertices())
            }
        if edges:
            edges_indexed = [
                (self.vnamelup[name1], self.vnamelup[name2])
                for name1, name2 in edges
            ]
        else:
            if 'max_random_edges' in kwargs:
                max_edges = range(kwargs['max_random_edges'])
            else:
                max_edges = range(size*2)
            random_edges = [
                random.sample(range(size), 2) for _ in max_edges
            ]
            edges_indexed = [
                (first, second)
                for first, second in random_edges
            ]
        self.g.add_edge_list(edges_indexed)

        self.vload = self.g.new_vertex_property('object')
        if 'load' in kwargs:
            for v, l in zip(self.g.vertices(), kwargs['load']):
                self.vload[v] = l
        else:
            for v in self.g.vertices():
                self.vload[v] = []

        if 'loadargs' in kwargs:
            self.vloadargs = self.g.new_vertex_property('vector<float>')
            for v, la in zip(self.g.vertices(), kwargs['loadargs']):
                self.vloadargs[v] = la

        self.vweight = self.g.new_edge_property('float')
        if 'weight' in kwargs:
            for e, w in zip(self.g.edges(), kwargs['weight']):
                self.vweight[e] = w
        else:
            for e in self.g.edges():
                self.vweight[e] = 1

        self.vinside = self.g.new_vertex_property('object')
        if 'inside' in kwargs:
            for v, i in zip(self.g.vertices(), kwargs['inside']):
                self.vinside[v] = i
        else:
            for v in self.g.vertices():
                self.vinside[v] = deque([])

        self.vontrack = self.g.new_vertex_property('object')
        if 'ontrack' in kwargs:
            for v, o in zip(self.g.vertices(), kwargs['ontrack']):
                self.vontrack[v] = o
        else:
            for v in self.g.vertices():
                self.vontrack[v] = deque([])

    def get_route(self, src, dst, **kwargs):
        """
        Returns list with route from `source` to `destination`

        Arguments
        ------
        src: int or str
            starting point of route, can be vertex name or vertex index.
        dst: int or str
            final point of route, can be vertex name or vertex index

        Returns
        ------
        route: collections.deque
            deque of vertex indices of the route from `src` to `dst`
        """

        # separate checks to allow source and destination to be
        # type-independant
        try:
            source = int(src)
        except ValueError:
            source = self.namelup[src]
        except TypeError:
            raise TypeError(
                'expected source to be vertex name or vertex index. '
                'got {}'.format(type(src))
            )
        try:
            target = int(dst)
        except ValueError:
            target = self.namelup[dst]
        except TypeError:
            raise TypeError(
                'expected destination to be vertex name or vertex index. '
                'got {}'.format(type(src))
            )

        route = deque([target])
        sg = gt.search.dijkstra_iterator(
                self.g, self.vweight, source=source, array=True)
        while route[0] != source:
            found = False
            for check_src, check_dest in sg:
                if check_dest == target:
                    route.appendleft(check_src)
                    target = check_src
                    found = True
            if not found:
                raise RuntimeError('cannot find route')
        return route

    def move_cars(self):
        """
        Attempts to move cars to the next vertex in their route

        Iterates over all vertices in `g`
        """

        for v in self.g.vertices():
            for _ in range(len(self.vontrack[v])):
                car = self.vontrack[v].popleft()
                if car.can_move:
                    # popleft next vertex from route
                    try:
                        nextvert = car.route.popleft()
                    except IndexError:
                        print(
                            'Car #{0} reached destination at {1}: {2}'.format(
                                car.id, self.g.vertex_index[v], self.vname[v]
                            )
                        )
                        nextvert = None
                    if nextvert:
                        if car.namelup:
                            nextvert = self.namelup[nextvert]
                        # since graph is not directional, doesn't matter if we
                        # use get_in_neighbors or get_out_neighbors
                        neighbors = self.g.get_in_neighbors(self.g.vertex(v))
                        if nextvert in neighbors:
                            self.vontrack[nextvert].append(car)
                            car.cur = nextvert
                            car.can_move = False
                        else:
                            raise RuntimeWarning(
                                'car#{0} is stuck at vertex {1}: {2}'.format(
                                    car.id,
                                    self.g.vertex_index[v],
                                    self.vname[v]
                                )
                            )
                else:
                    self.vontrack[v].append(car)
        # unlock all cars for next step
        for v in self.g.vertices():
            for car in self.vontrack[v]:
                car.can_move = True

    def spawn_car(self, target, amount, **kwargs):
        """
        Creates amount of `Car` objects in vertex

        Arguments
        ------
        target: str or int
            vertex name or vertex index of target where objects should be
            spawned
        amount: int
            how many objects to spawn

        Kwargs
        -----
        route: collections.deque([int])
            route deque. Using `get_route` method is recommended. `route` and
            `dst` are self-exclusive, if both are provided, `route` takes
            priority. If neither `route` nor `dst` are provided, the route
            is randomly generated. Route must include current station.
        dst: str or int
            car travel destination. Can be vertex name or vertex index. `route`
            and `dst` are self-exclusive, if both are provided, `route` takes
            priority. If neither `route` nor `dst` are provided, the route
            is ramdomly generated.
        other kwargs are passed to `Car` object
        """

        try:
            target = int(target)
        except ValueError:
            # assume it is vertex name
            try:
                target = self.namelup[target]
            except KeyError:
                raise KeyError('nonexistant vertex name {}'.format(target))
        except TypeError:
            raise TypeError(
                'target expected to be iter(str) or iter(int). '
                'got {}'.format(type(route))
            )
        if 'route' in kwargs:
            route = kwargs.pop('route')
        elif 'dst' in kwargs:
            route = self.get_route(target, kwargs.pop('dst'))
        else:
            dst = np.random.choice(np.delete(self.g.get_vertices(), target))
            route = self.get_route(target, dst)
        for _ in range(amount):
            car = Car(route, **kwargs)
            self.vontrack[target].append(car)


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
    id: long
        unique identification number of the car.
    total: [long]
        `id` that was assigned to the last created car, represents total
        amount of cars created
    can_move: bool
        if True, car can be moved to another vertex. Required for proper car
        movement restraint during step evaluation

    Methods
    ------
    """

    total = [0]

    def __init__(self, route, size=20, **kwargs):
        """
        Initialize Car.

        Args
        ------
        route: collections.deque(str) or collections.deque(int)
            route to follow, must contain either vertex names or vertex indices
        size: int
            car passenger capacity. Default: 20

        Kwargs
        ------
        inside: int
            starting amount of passengers. Default: 0
        cur: str or int
            starting position of car. Avoid using this argument unless you know
            what you are doing, because this may lead to stuck cars.  `cur`
            must be same type as `route` to avoid improper `namelup`
            assignment. Default: `route[0]`
        """

        self.id = self.total[0]
        self.total[0] += 1
        self.size = size
        self.namelup = False
        self.can_move = True
        if 'amount' in kwargs:
            self.inside = kwargs['amount']
        else:
            self.inside = 0

        # try to convert list elements into vertex indices
        try:
            self.route = deque([int(item) for item in route])
        except ValueError:
            # assume it is vertex names
            self.route = route
            self.namelup = True
        except TypeError:
            raise TypeError(
                'route expected to be iter(str) or iter(int). '
                'got {}'.format(type(route))
            )
        if 'cur' in kwargs:
            try:
                self.cur = int(cur)
            except ValueError:
                # assume it is vertex name
                self.cur = cur
                self.namelup = True
            except TypeError:
                raise TypeError(
                    'route expected to be iter(str) or iter(int). '
                    'got {}'.format.type(route)
                )
        else:
            self.cur = self.route.popleft()

    def step():
        """
        Step evaluation

        Car attempts to follow a path to the next vertex in route.

        Arguments
        ------
        none

        Returns
        ------
        status: int
            execution status.
            0 - car arrived to new location
            1 - car at the end of the route
            2 - unable to traverse further
        """

        try:
            nextvert = self.route.popleft()
        except IndexError:
            # car is at the endpoint
            return 1


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
    id: long
        unique identification number of the passenger.
    total: [long]
        `id` that was assigned to the last created passenger, represents total
        amount of passengers created

    Methods
    ------
    """

    total = [0]

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
            current passenger position. Avoid using this argument unless you
            know what you are doing, because this may lead to stuck passengers.
            `cur` must be same type as `route` to avoid improper `namelup`
            assignment. Default: `route[0]`
        """

        # assign id and increment total
        self.id = self.total[0]
        self.total += 1
        self.namelup = False
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

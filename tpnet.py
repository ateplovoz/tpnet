"""
======
tpnet.py
main module

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

Requires
------
random (standard)
collections (standard)
numpy
graph_tool

db.py

Classes
------
Net - class for graph network and related functions
Car - class that navigates Net and transfers Passenger
Passenger - class that represents a passenger
"""

import random
from collections import deque
import numpy as np
import graph_tool as gt

from db import new_db, log


# TODO: remove vload, it duplicates vinside
class Net:
    """
    Transport network class

    Variables
    ------
    g: graph_tool.Graph
        `Graph` object that contains all information about network.
    vname: graph_tool.PropertyMap (type: string)
        vertex names. Might be absent if no names were provided to constructor.
    namelup: dict
        dictionary that provides index lookup by name.
    vload: graph_tool.PropertyMap (type: object)
        current load of each vertex.
    vloadargs: graph_tool.PropertyMap (type: vector<float>)
        attributes of function for periodic load change.
    vinside: graph_tool.PropertyMap (type: object)
        deque of `Passenger` objects inside of each `g` vertex.
    vontrack: graph_tool.PropertyMap (type: object)
        deque of `Car` objects inside of each `g` vertex.
    venroute: graph_tool.PropertyMap (type: object)
        deque of `Car` objects in transition between vertices (on edges of
        `g`).
    allcars: dict
        dictionary that contains all spawned `Car` objects
    allpassengers: dict
        dictionary that contains all spawned `Passenger` objects

    Methods
    ------
    get_route:
        returns deque of vertex indices that form route from one vertex to
        another.
    move_cars:
        attempts to move `Car` objects in vertex's `vontrack`.
    spawn_car:
        spawns `Car` objects at target vertex.
    spawn_passenger:
        spawns `Passenger` objects at target vertex.
    ptransfer:
        moves `Passenger` objects from and into cars.
    getstat:
        returns array with statistics
    """

    def __init__(self, size, names=None, edges=None, **kwargs):
        """
        Initialize Net

        Args
        ------
        size: int
            number of vertices in graph.
        names: iter(str)
            list of vertex names, optional.
        edges: iter(tuple(str, str))
            list of edges between vertices.

        Kwargs
        ------
        max_random_edges: int
            amount of random edges to generate. Default: `size`*2.
        load: iter(`Passenger`)
            iterator of starting load for vertices. Must contain Passenger
            class objects. Default: [].
        loadargs: iter(tuple(float, float))
            iterator of (frequency, offset) of periodic load function, must be
            size of `size`. This influences on how many Passenger-class objects
            to spawn on next iteration. Default: None.
        weight: iter(float)
            weight property of `g` edges. Must be size of `edges` or `size*2`
            if `edges` is None. Default: 1.
        inside: iter(collections.deque(`Passenger`))
            starting passengers. Must be an iterable that contains deques with
            `Passenger` objects for each vertex. Passengers are assigned
            according to vertex index. Default: collections.deque([]).
        ontrack: iter(iter(`Car`))
            starting cars. Must be an iterable that contains deques with `Car`
            objects for each vertex. Cars are assigned according to vertex
            index. Default: collections.deque([]).
        enroute: iter(s, t, iter(`Car`))
            Starting cars in transition between vertices.  Must be an iterable
            that contains starting edge vertex, ending edge vertex and a deque
            with `Car` objects. Default: collections.deque([]).

        """

        self.g = gt.Graph(directed=False)
        self.g.add_vertex(size)
        self.allcars = {}
        self.allpassengers = {}
        new_db()

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
                (self.namelup[name1], self.namelup[name2])
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

        self.venroute = self.g.new_edge_property('object')
        if 'enroute' in kwargs:
            for vin, vout, ed in kwargs['enroute']:
                self.venroute[self.g.edge(vin, vout)] = ed
        else:
            for e in self.g.edges():
                self.venroute[e] = deque([])

    def get_route(self, src, dst, **kwargs):
        """
        Returns list with route from `source` to `destination`

        Arguments
        ------
        src: int or str
            starting point of route, can be vertex name or vertex index.
        dst: int or str
            final point of route, can be vertex name or vertex index.

        Kwargs
        ------
        none yet.

        Returns
        ------
        route: collections.deque
            deque of vertex indices of the route from `src` to `dst`.
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

    def move_cars(self, unlock=True):
        """
        Evaluates all vertices and attempts to move `Car` object in `vontrack`
        deque along their paths.

        Moves `Car` objects in two steps. First, checks the edges for cars in
        transition. Any cars found will be transferred to according vertices
        and locked.  At second step checks the vertices for cars that can move
        along route.  If found, transfers them to according edge and locks
        them. After finishing, if `unlock` is True, unlocks all cars.

        Stuck cars raise RuntimeError and are despawned after. If car reaches
        destination, print message and despawn car.

        Arguments
        ------
        unlock: bool
            if True, unlocks all cars after moving. Default: True.

        Returns
        ------
        nuffin.
        """

        for e in self.g.edges():
            for _ in range(len(self.venroute[e])):
                car = self.venroute[e].popleft()
                if car.can_move:
                    nextvert = car.route.popleft()
                    if car.namelup:
                        nextvert = self.namelup[nextvert]
                    self.vontrack[nextvert].append(car)
                    car.chcur(nextvert, self.vname[nextvert])
                    car.can_move = False
        for v in self.g.get_vertices():
            for _ in range(len(self.vontrack[v])):
                car = self.vontrack[v].popleft()
                if car.can_move:
                    # popleft next vertex from route
                    try:
                        nextvert = car.route[0]
                    except IndexError:
                        print(
                            'Car #{0} reached destination at {1}: {2}'.format(
                                car.id, v, self.vname[v]
                            )
                        )
                        log(
                            'i reached destination at {1}: {2}'.format(
                                car.id, v, self.vname[v]
                            ), 'car', car.id
                        )
                        nextvert = None
                    if nextvert:
                        if car.namelup:
                            nextvert = self.namelup[nextvert]
                        # since graph is not directional, doesn't matter if we
                        # use get_in_neighbors or get_out_neighbors
                        neighbors = self.g.get_in_neighbors(self.g.vertex(v))
                        if nextvert in neighbors:
                            e = self.g.edge(v, nextvert)
                            self.venroute[e].append(car)
                            car.chcur(
                                '{0}-{1}'.format(v, nextvert),
                                '{0}-{1}'.format(
                                    self.vname[v],
                                    self.vname[nextvert]
                                )
                            )
                            car.can_move = False
                            # TODO: notify car passengers that it arrived to
                            # next station
                        else:
                            raise RuntimeWarning(
                                'car#{0} is stuck at vertex {1}: {2}'.format(
                                    car.id, v, self.vname[v]
                                )
                            )
                            log(
                                'i am stuck at vertex {1}: {2}'.format(
                                    car.id, v, self.vname[v]
                                ), 'car', car.id
                            )
                else:
                    self.vontrack[v].append(car)
        # unlock all cars for next step
        for v in self.g.vertices():
            for car in self.vontrack[v]:
                car.can_move = True
        for e in self.g.edges():
            for car in self.venroute[e]:
                car.can_move = True

    def spawn_car(self, target, **kwargs):
        """
        Creates `Car` objects at `target` vertex and places them in `vontrack`.

        Arguments
        ------
        target: str or int
            vertex name or vertex index of target where objects should be
            spawned.

        Kwargs
        -----
        amount: int
            how many objects to spawn.
        route: collections.deque([int])
            route deque. Using `get_route` method is recommended. `route` and
            `dst` are self-exclusive, if both are provided, `route` takes
            priority. If neither `route` nor `dst` are provided, the route is
            randomly generated for each object. Route must include current
            station.
        dst: str or int
            car travel destination. Can be vertex name or vertex index. `route`
            and `dst` are self-exclusive, if both are provided, `route` takes
            priority. If neither `route` nor `dst` are provided, the route
            is ramdomly generated for each object.
        other kwargs are passed to a `Car` object.

        Returns
        ------
        nuffin.
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
                'got {}'.format(type(target))
            )
        if 'amount' in kwargs:
            amount = kwargs['amount']
        else:
            amount = 1
        for _ in range(amount):
            if 'route' in kwargs:
                route = kwargs.pop('route')
            elif 'dst' in kwargs:
                route = self.get_route(target, kwargs.pop('dst'))
            else:
                dst = np.random.choice(
                    np.delete(self.g.get_vertices(), target)
                )
                route = self.get_route(target, dst)
            car = Car(route, **kwargs)
            self.vontrack[target].append(car)
            self.allcars[car.id] = car
            log(
                'created at {0}: {1} with destination {2}: {3}'.format(
                    target, self.vname[target],
                    car.get_last(), self.vname[car.get_last()]
                ),
                'car', car.id
            )

    def spawn_passenger(self, target, **kwargs):
        """
        Creates `Passenger` objects at `target` vertex and places them in
        `vinside`.

        Arguments
        ------
        target: str or int
            vertex name or vertex index of target where objects should be
            spawned.

        Kwargs
        -----
        amount: int
            how many objects to spawn.
        route: collections.deque([int])
            route deque. Using `get_route` method is recommended. `route` and
            `dst` are self-exclusive, if both are provided, `route` takes
            priority. If neither `route` nor `dst` are provided, the route is
            randomly generated for each object. Route must include current
            station.
        dst: str or int
            object travel destination. Can be vertex name or vertex index.
            `route` and `dst` are self-exclusive, if both are provided, `route`
            takes priority. If neither `route` nor `dst` are provided, the
            route is ramdomly generated for each object.
        other kwargs are passed to a `Passenger` object.

        Returns
        ------
        nuffin.
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
                'target expected to be str or int. '
                'got {}'.format(type(target))
            )
        if 'amount' in kwargs:
            amount = kwargs['amount']
        else:
            amount = 1
        for _ in range(amount):
            if 'route' in kwargs:
                route = kwargs.pop('route')
            elif 'dst' in kwargs:
                route = self.get_route(target, kwargs.pop('dst'))
            else:
                dst = np.random.choice(
                    np.delete(self.g.get_vertices(), target)
                )
                route = self.get_route(target, dst)
            pgr = Passenger(route, **kwargs)
            self.vinside[target].append(pgr)
            self.allpassengers[pgr.id] = pgr
            log('created at {0}: {1} with destination {2}: {3}'.format(
                target, self.vname[target],
                pgr.get_last(), self.vname[pgr.get_last()]
            ), 'pgr', pgr.id)

    def ptransfer(self, targets=None):
        """
        Transfers `Passenger` objects from and into `Car` objects.

        First, gets all `Passenger` objects from `Car` objects (in `vontrack`
        at vertex) that have this station as destination. Then checks
        `Passenger` objects (in `vinside` at vertex) if they should get into
        `Car` object to move along their route.

        Arguments
        ------
        target: iter(str) or iter(int)
            Can be provided to check only specified sequence of vertices. List
            elements can be vertex indices or vertex names.

        Kwargs
        ------
        none yet.

        Returns
        ------
        ptransfer: iter(`Passenger`)
            iterator of `Passenger` objects.
        """
        if targets:
            try:
                targets = [int(item) for item in targets]
            except ValueError:
                # assume it is vertex name
                try:
                    targets = [self.namelup[item] for item in targets]
                except KeyError:
                    raise KeyError(
                        'nonexistant vertex name {}'.format(targets)
                    )
            except TypeError:
                raise TypeError(
                    'targets expected to be iter(str) or iter(int). '
                    'got {}'.format(type(targets))
                )
        else:
            targets = self.g.get_vertices()
        for v in targets:
            ptransfer = np.array([], dtype='object')
            # get all passengers that need transfer or at final destination and
            # place them in buffer
            for car in self.vontrack[v]:
                ptransfer = np.append(
                    ptransfer,
                    car.peject(v)
                )
            for _ in range(len(self.vinside[v])):
                p = self.vinside[v].popleft()
                # route item will be popped at arrival to the next vertex
                nextvert = p.get_next()
                if p.namelup:
                    nextvert = self.namelup[nextvert]
                # TODO: too much if?
                # check if we arrived to the last stop
                if nextvert != v:
                    found = False
                    for car in self.vontrack[v]:
                        # check if car full
                        if not len(car.inside) >= car.size:
                            # TODO: passengers should take cars that have their
                            # next route vertex as next stop instead of hoping
                            # that they will eventually arrive
                            if nextvert in car.route:
                                car.inside.append(p)
                                found = True
                                # log message as passenger TODO: move it to
                                # Passenger class somehow
                                log('mounting car {0} at {1}:{2}'.format(
                                    car.id, v, self.vname[v]
                                ), 'pgr', p.id)
                                break
                    if not found:
                        # place it back and hope for the best
                        self.vinside[v].append(p)
                else:
                    print('Passenger #{0} at the destination {1}: {2}'.format(
                        p.id, v, self.vname[v]
                    ))
                    log('i am at the destination {1}: {2}'.format(
                            p.id, v, self.vname[v]
                    ), 'pgr', p.id)
            # assign all passengers from buffer to vertex
            if ptransfer.size:
                for p in ptransfer:
                    newcur = p.get_next()
                    p.chcur(newcur, self.vname[newcur])
                    p.route.popleft()
                    self.vinside[v].append(p)

    def getstat(self, what='net', h=False):
        """
        Returns array with statistics.

        For now can return statistics about graph, cars or passengers.

        Array order:
            net: v, vname, len(vinside), len(vontrack).
            car: id, cur, route[-1], size, len(inside).
            pgr: id, cur, route[-1].

        Arguments
        ------
        what: str
            what kind of statistics to return. Possible options are 'net',
            'car', 'pgr'.
        h: bool
            stands for 'human readable'. If True then returns vertex names
            instead of vertex indices

        Returns
        ------
        stat: numpy.ndarray
            array with statistics.
        """

        stat = np.array([])
        if what == 'net':
            for v in self.g.get_vertices():
                cols = [
                    v, self.vname[v], len(self.vinside[v]),
                    len(self.vontrack[v])
                ]
                stat = np.append(stat, cols)
            if stat:
                stat = stat.reshape(len(self.g.get_vertices()), len(cols))
        elif what == 'car':
            for _, c in self.allcars.items():
                if h:
                    # make it human readable
                    try:
                        int(c.cur)
                        intransition = False
                    except ValueError:
                        # car in transition and have `cur` format as `s-t`
                        intransition = True
                        s_vert, t_vert = c.cur.split('-')
                    if intransition:
                        ccur = '{0}-{1}'.format(
                            self.vname[s_vert], self.vname[t_vert]
                        )
                    else:
                        ccur = self.vname[c.cur]
                    cols = [
                        c.id, ccur, self.vname[c.get_next()],
                        self.vname[c.get_last()], c.size, len(c.inside)
                    ]
                else:
                    cols = [
                        c.id, c.cur, c.get_next(), c.get_last(),
                        c.size, len(c.inside)
                    ]
                stat = np.append(stat, cols)
            if stat.size:
                stat = stat.reshape(len(self.allcars), len(cols))
        elif what == 'pgr':
            for _, p in self.allpassengers.items():
                if h:
                    # make it human readable
                    cols = [
                        p.id, self.vname[p.cur], self.vname[p.get_next()],
                        self.vname[p.get_last()]
                    ]
                else:
                    cols = [
                        p.id, p.cur, p.get_next(), p.get_last()
                    ]
                stat = np.append(stat, cols)
            if stat.size:
                stat = stat.reshape(len(self.allpassengers), len(cols))
        return stat


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
    peject:
        returns `Passenger` objects for ejection
    get_next:
        attepmts to return next destination in `route`
    get_last:
        attempts to return last destination in `route`
    chcur:
        changes `cur` — current location, logs change
    """

    total = [0]

    def __init__(self, route, size=20, **kwargs):
        """
        Initialize Car.

        Args
        ------
        route: collections.deque(str) or collections.deque(int)
            route to follow, must contain either vertex names or vertex
            indices.
        size: int
            car passenger capacity. Default: 20.

        Kwargs
        ------
        inside: collections.deque(`Passenger`)
            starting passengers inside of car. Must be deque, containing
            `Passenger` objects. Default: deque([]).
        cur: str or int
            starting position of car. Avoid using this argument unless you know
            what you are doing, because this may lead to stuck cars.  `cur`
            must be same type as `route` to avoid improper `namelup`
            assignment. Default: `route[0]`.
        """

        self.id = self.total[0]
        self.total[0] += 1
        self.size = size
        self.namelup = False
        self.can_move = True
        if 'amount' in kwargs:
            self.inside = kwargs['amount']
        else:
            self.inside = deque([])
        # try to convert list elements into deque of vertex indices
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
                self.cur = int(kwargs['cur'])
            except ValueError:
                # assume it is vertex name
                self.cur = kwargs['cur']
                self.namelup = True
            except TypeError:
                raise TypeError(
                    'route expected to be iter(str) or iter(int). '
                    'got {}'.format(type(route))
                )
        else:
            self.cur = self.route.popleft()

    def peject(self, current):
        """
        returns array of `Passenger` objects (taken from `inside` attribute)
        that need to transfer to different car or reached final destination.

        Arguments
        ------
        current: str or int
            current vertex. Is compared to `cur` attribute so passengers don't
            get ejected at edges or wrong vertices. If `namelup` is True,
            `current` must be a vertex name. Otherwise it must be a vertex
            index.

        Returns
        ------
        ptransfer: numpy.ndarray(`Passenger`)
            an array of `Passenger` objects taken from `inside` attribute.
        """

        if self.cur != current:
            raise RuntimeError(
                'Car #{0} is at unexpected location.'
                'Expected {1}, got {2}.'.format(self.id, self.cur, current)
            )
        ejecting = np.array([], dtype='object')
        nextvert = self.get_next()
        for _ in range(len(self.inside)):
            p = self.inside.popleft()
            # check if next destination in route and we will eventually arrive
            # TODO: fix this so passengers can be more picky about cars
            if not p.get_next() in self.route:
                ejecting = np.append(ejecting, p)
                # put message in log as passenger
                log('ejected from car {0}'.format(self.id), 'pgr', p.id)
            else:
                self.inside.append(p)
        # put message in log as car
        log(
            'ejecting passengers: {0}'.format([p.id for p in ejecting]),
            'car', self.id
        )
        return ejecting

    def get_next(self):
        """
        Attempts to return next destination in `route`. If cannot, returns
        current position
        """
        try:
            nextvert = self.route[0]
        except IndexError:
            # nowhere to go - return current station
            nextvert = self.cur
        return nextvert

    def get_last(self):
        """
        Attempts to return last destination in `route`. If cannot, returns
        current position
        """
        try:
            nextvert = self.route[-1]
        except IndexError:
            # nowhere to go - return current station
            nextvert = self.cur
        return nextvert

    def chcur(self, newcur, newcurname=None):
        """
        Changes `cur` value to a `newcur`. Writes change in database

        If `namelup` is True, then, for consistency, write `cur` as vertex
        name.
        """
        if self.namelup and newcurname:
            self.cur = newcurname
        else:
            self.cur = newcur
        log('i am at {0}: {1}'.format(newcur, newcurname), 'car', self.id)


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
        amount of passengers created.

    Methods
    ------
    get_next:
        attepmts to return next destination in `route`
    get_last:
        attempts to return last destination in `route`
    chcur:
        changes `cur` — current location, logs change
    """

    total = [0]

    def __init__(self, route, **kwargs):
        """
        Initialize Passenger.

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
            assignment. Default: `route[0]`.
        """

        # assign id and increment total
        self.id = self.total[0]
        self.total[0] += 1
        self.namelup = False
        # try to convert list elements into deque of vertex indices
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
            self.cur = kwargs['cur']
        else:
            self.cur = self.route.popleft()

    def get_next(self):
        """
        Attempts to return next destination in `route`. If cannot, returns
        current position
        """
        try:
            nextvert = self.route[0]
        except IndexError:
            # nowhere to go - return current station
            nextvert = self.cur
        return nextvert

    def get_last(self):
        """
        Attempts to return last destination in `route`. If cannot, returns
        current position
        """
        try:
            nextvert = self.route[-1]
        except IndexError:
            # nowhere to go - return current station
            nextvert = self.cur
        return nextvert

    def chcur(self, newcur, newcurname=None):
        """
        Changes `cur` value to a `newcur`. Writes change in database

        If `namelup` is True, then, for consistency, write `cur` as vertex
        name.
        """
        if self.namelup and newcurname:
            self.cur = newcurname
        else:
            self.cur = newcur
        log('i am at {0}: {1}'.format(newcur, newcurname), 'pgr', self.id)

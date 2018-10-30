# TPNet — Transport Net simulation model

## Introduction

This project is oriented towards creation and simulation of generic transport
net. Transport net is represented by non-directed graph with vertex being
transport stations and edges being commutation lines.

Net by itself provides graph topology and means of transportation.
Transportation itself is performed by objects called "cars". And cars
themslelves transfer basic objects called "passengers". Each car and each
passenger have their own route that can be determined manually by specifying
route vertex or simply destination vertex. If no route is provided, then random
route is generated for each car and passenger created.

The goal of this project is to simulate automated transport net that can be
controlled externally. Future of this project includes developing simple API
for object creation or graph modification, imitation of real transport networks
(such as Moscow Metro) and developing AI system for control and optimization.

### Requirements

This module is built upon `graph-tool` package. It is necessary to build and
install in order to use this module. Package can be found on [main
site](https://graph-tool.skewed.de) and installation instructions can be found
[here](https://git.skewed.de/count0/graph-tool/wikis/installation-instructions)

## Quick start

`tpnet.py` provides means of creating and controlling `Net`, `Car` and
`Passenger` classes, as well as gathering information about their position and
route.

To create a net one must call `Net` class constructor and provide arguments for
desired net topology (see docstrings of `Net.__init__`). Cars are created
via `Net.spawn_car` method and, similarly, passengers are created via
`Net.spawn_passenger` method. Those functions should work consistenly when
provided with either vertex names or vertex indices.

Net class is able to convert vertex indices to vertex name and vice-versa with
`Net.vname[<vertex index>]` and `Net.namelup[<vertex name>]` attributes.

For information purposes there are `Net.getstat` function that returns vertex,
cars or passengers statistics tables. If needed, one can access `Net.allcars`
and `Net.allpassengers` dictionaries to get access to all created cars or
passengers.



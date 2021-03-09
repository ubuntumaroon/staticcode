Routing
================

Routing optimization project based on Google OR-tools and OSRM table service.

Requirements
------------

Python 3.8+.
Google OR-tools
OSRM table services running on port:5000

How to use
----------
.. code-block:: python

    from routing.solver import Solver

    result = Solver.solve(data)
    result.json()   # convert to json


This package use Pydantic models for input and output data.
Please refer to the Request models for input data,
and Response models for output

Options:

* No need to assign vehicle start point. The algorithm will optimize start points.
* Set penalties in Optimization, to turn on/off drop node options and how to reduce number of vehicles
* Runs faster with more restrictions




.. note::
  Todo:

Dependencies
------------

Dependencies are defined in:

- ``requirements.in``

- ``requirements.txt``

- ``dev-requirements.in``

- ``dev-requirements.txt``

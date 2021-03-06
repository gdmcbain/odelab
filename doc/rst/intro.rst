.. _Getting_started:

Getting Started
***************

|project| is a Python library for solving differential equations.

There is support for

* easily solving generic differential equations using one of the many methods already provided in |project|
* solve differential equations of a *special structure*, such as differential-algebraic equations, and equations arising in mechanics
* easily create your own custom numerical schemes


Differential Equations
======================

Differential Equations in Mathematics
-------------------------------------

A *differential equation* is a problem of the following kind.
One is looking for a function :math:`u` which fulfills the following property:

.. math::

    u'(t) = f(t,u(t)) \qquad \forall t ≥ 0

Such a problem has many solutions, so one must also prescribe an *initial condition*:

.. math::

    u(0) = u_0

The data of the function :math:`f` and of the initial condition :math:`u_0` guarantee in general the existence and uniqueness of the solution.

Solving Differential Equations Numerically
------------------------------------------

In order to solve a differential equation numerically, we need a *numerical scheme*.
The simplest numerical scheme is the explicit Euler method, described as follows:

.. math::

    u_{n+1} = u_{n} + h f(t_n, u_n)

Given an initial condition :math:`u_0`, the explicit Euler method successively creates :math:`u_1`, :math:`u_2`, etc.
Notice that one has to specify a *time step* :math:`h` for this method to work.

|project| comes with many such schemes, and makes it very easy to create new ones, see :ref:`scheme_chapter`.


Step-by-step Example
--------------------

Let us examine a simple example.
Suppose we want to solve the problem

.. math::

    u' = -u

with the initial condition

.. math::

    u(0) = u_0 = 1

We first have to define the *system*, that is, the right hand side of the differential equation.
This is done as follows::

    from odelab import System

    def f(t,u):
        return -u

    system = System(f)

The next thing we need is to choose a *numerical method* to solve that differential equation.
Let us choose a very simple scheme, the *explicit Euler* scheme.
Most numerical schemes require a *time step*.
We choose here a time step of :math:`0.1`.
This is done as follows::


    from odelab.scheme.classic import ExplicitEuler
    scheme = ExplicitEuler(0.1) # Explicit Euler scheme with time step 0.1


Now we have to set-up a solver object that will take care of running the simulation and storing the resulting computations::

    from odelab import Solver
    s = Solver(scheme=scheme, system=system) # we use the scheme and system variables defined earlier
   
We still need to specify the initial condition for this simulation::

    s.initialize(u0=1.)

Finally, we can run the simulation from :math:`t=0` to :math:`t=1` with the following call::

    s.run(1.)

To summarize what we have up to now, the whole code is the following:

.. literalinclude:: ../code/explot.py
    :tab-width: 4


.. plot:: code/explot.py


.. _vanderpol_example:

Example with Plot
-----------------

.. topic:: Example: Solving the van der Pol equation

    Here is an example of solving the van der Pol equations with a Runge-Kutta method and then plotting the result with ``plot2D``.
    See :ref:`simulation_name` and :ref:`plot2d` for more information.

    .. plot:: code/vanderpol.py
        :include-source:

Architecture
============

|project| is built on a very simple architecture.
The main classes are :class:`Solver`, :class:`Scheme` and :class:`System`.

 * :class:`Solver` takes care of initializing, running and storing the result of a simulation
 * :class:`System` models a right hand side, which may be just a function, or a partitioned system, or even a DAE.
 * :class:`Scheme` models a method to solve the equation. It may be explicit or implicit, adaptive or not, it is all up to you.





# -*- coding: UTF-8 -*-
from __future__ import division


from odelab.scheme import *
from odelab.scheme.exponential import *

from odelab.system import *
from odelab.solver import *
import odelab.newton as rt

import tempfile
import os

import numpy as np
import numpy.testing as npt
import nose.tools as nt
from nose.plugins.skip import SkipTest

import pylab as pl
pl.ioff()

Solver.catch_runtime = False

class DummySystem(System):
	def __init__(self, f):
		super(DummySystem,self).__init__(f)

	def label(self, component):
		return ['x', 'y'][component]

	def output(self, ut):
		return np.ones(ut.shape[1])

	def exact(self, t, e0):
		x,y,t0 = e0
		c,s = np.cos(t), np.sin(t)
		return np.vstack([c*x-s*y, s*x + c*y])


def rotational(t,u):
	"""
	Rotational vector field
	"""
	return array([-u[1], u[0]])

def quick_setup(plotter, **kwargs):
	for k,v in kwargs.items():
		setattr(plotter,k,v)

class Harness_Circle(object):
	def setUp(self):
		self.f = rotational
		self.make_solver()
		self.s.initialize(u0 = array([1.,0.]), h=.01, time = 10.)
		self.s.run()

	def test_plot_2D(self):
		pl.clf()
		a = self.s.plot(1,time_component=0).axis
		nt.assert_equal(a.get_xlabel(), 'x')
		self.s.plot2D()
		for l in a.get_lines():
			d = l.get_data()
			radii = np.abs(np.sqrt(d[0]**2+d[1]**2) - 1)
			assert np.all(radii < .2) # should roughly be a circle

	def test_plot(self):
		a = self.s.plot(plot_exact=False).axis
		nt.assert_equal(a.get_xlabel(), 'time')
		self.s.plot(plot_exact=True)
		tmp = tempfile.gettempdir()
		path = os.path.join(tmp, 'test_fig.pdf')
		print path
		plotter = Plotter(self.s)
		plotter.savefig(path)
		quick_setup(plotter, components=['output', 0], plot_exact=False)
		plotter.savefig(path)
		nt.assert_equal(len(plotter.axis.lines), 2)
		quick_setup(plotter, components='output',)
		plotter.savefig(path)
		quick_setup(plotter, components=['output', 0], plot_exact=True)
		plotter.savefig(path)
		nt.assert_equal(len(plotter.axis.lines), 4)
		# the following should be tested:
		self.s.plot(components=['output'], error=True)
		self.s.plot_function('output')

class Test_Circle_EEuler(Harness_Circle):
	def make_solver(self):
		self.s = SingleStepSolver(ExplicitEuler(), DummySystem(self.f))

class Test_Circle_IEuler(Harness_Circle):
	def make_solver(self):
		self.s = SingleStepSolver(ImplicitEuler(), DummySystem(self.f))


class Test_Circle_RK34(Harness_Circle):
	def make_solver(self):
		self.s = SingleStepSolver(RungeKutta34(), DummySystem(self.f))
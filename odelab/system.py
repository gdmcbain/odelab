# -*- coding: UTF-8 -*-
"""
:mod:`System` -- Systems
============================

Examples of ODE systems.

Collection of subclasses of the class :class:`odelab.system.System`.
The interface needed depends on the solver. For example, exponential solvers will need a `linear` method,
dae solvers will need a `constraint`, or `multi-dynamics` method. See the documentation of the :doc:`scheme`
section for more information.

.. module :: system
	:synopsis: Examples of ODE systems.
.. moduleauthor :: Olivier Verdier <olivier.verdier@gmail.com>

"""
from __future__ import division

import numpy as np
from numpy import array

import scipy.sparse as sparse

import odelab.scheme.rungekutta as rk

class System(object):
	"""
	General System class to define a simple dynamics given by a right-hand side.
	"""
	def __init__(self, f=None):
		if f is not None:
			self.f = f

	def label(self, component):
		return '%d' % component

	def preprocess(self, u0):
		return u0

	def postprocess(self, u1):
		return u1

	def velocity(self,u):
		r"""select the velocity component
		It may be interpreted as :math:`\frac{∂H}{∂p}`"""

	def position(self, u):
		"""select the position component"""

	def lag(self, u):
		"""select the lagrangian component"""

	def vel_lag_split(self, vl):
		"""splits between velocity and lagrangian"""

	def vel_lag_stack(self,v,l):
		"""stacks together the velocity and lagrangian parts"""

	def force(self, u):
		r"""compute the force as a function of `u`
		It may be interpreted as :math:`-\frac{∂H}{∂q}`"""

	def codistribution(self, u):
		"""compute the codistribution matrix at `u`"""


class JayExample(System):
	r"""
	 The example in [jay06]_ §5. This is a test to check implementation of the
	 SRK-DAE2 methods given in [jay06]_. We want to compare our results to
	 [jay06]_ Fig. 1.

	 The exact solution to this problem is known as is

.. math::

	y1(t) = \ee^t\\
	y2(t) = \ee^{-2t}\\
	z1(t) = \ee^{2t}

We will compute the global error at :math:`t=1` at plot this relative to the
stepsize :math:`h`. This is what is done in [jay06]_ Fig.1.


:References:

.. [jay06] Jay - *Specialized Runge-Kutta methods for index $ 2$ differential-algebraic equations.* Math. Comput. 75, No. 254, 641-654 (2006). :doi:`10.1090/S0025-5718-05-01809-0`
	"""


	def multi_dynamics(self, tu):
		y1,y2,z,t = tu
		return {
			rk.LobattoIIIA: array([y2 - 2*y1**2*y2, -y1**2]),
			rk.LobattoIIIB: array([y1*y2**2*z**2, np.exp(-t)*z - y1]),
			rk.LobattoIIIC: array([-y2**2*z, -3*y2**2*z]),
			rk.LobattoIIICs: array([2*y1*y2**2 - 2*np.exp(-2*t)*y1*y2, z]),
			rk.LobattoIIID: array([2*y2**2*z**2, y1**2*y2**2])
			}

	def constraint(self, tu):
		return array([tu[0]**2*tu[1] -  1])

	def state(self, u):
		return u[0:2]

	def lag(self, u):
		return u[2:3]

	@classmethod
	def exact(self, t, u0):
		if np.allclose(u0[:2], array([1.,1.])):
			return array([np.exp(t), np.exp(-2*t), np.exp(2*t)])
		raise ValueError("Exact solution not defined")

	def label(self, component):
		return ['y1','y2','z'][component]

class GraphSystem(System):
	r"""
	Trivial semi-explicit index 2 DAE of the form:

.. math::

		x' = 1\\
		y' = λ\\
		y  = f(x)
	"""

	def state(self, u):
		return u[:2]

	def lag(self, u):
		return u[2:3]

	def multi_dynamics(self, ut):
		x,y = self.state(ut)
		return {
			rk.RadauIIA: np.zeros_like(self.state(ut)),
			rk.RadauIIA: array([np.ones_like(x), self.lag(ut)[0]]),
			}

	def constraint(self, ut):
		x,y = self.state(ut)
		return array([y - self.f(x)])

	def hidden_error(self, t, u):
		return self.lag(u)[0] - self.f.der(t,self.state(u)[0])

	def exact(self, t, u0):
		x = u0[0] + t
		return array([x, self.f(x), self.f.der(x)])

class ODESystem(System):
	"""
	Simple wrapper to transform an ODE into a semi-explicit DAE.
	"""
	def __init__(self, f, RK_class=rk.LobattoIIIA):
		self.f = f
		self.RK_class = RK_class

	def state(self, u):
		return u[:1]

	def lag(self,u):
		return u[1:] # should be empty

	def multi_dynamics(self, tu):
		return {self.RK_class: array([self.f(tu)])}

	def constraint(self, tu):
		return np.zeros([0,np.shape(tu)[1]])


def tensordiag(T):
	if len(np.shape(T)) == 3: # vector case
		assert T.shape[1] == T.shape[2]
		T = np.column_stack([T[:,s,s] for s in range(np.shape(T)[1])])
	return T

class NonHolonomic(System):
	"""
	Creates a DAE system out of a non-holonomic one, suitable to be used with the :class:`odelab.scheme.constrained.Spark` scheme.
	"""
	def constraint(self, u):
		constraint = np.tensordot(self.codistribution(u), self.velocity(u), [1,0])
		constraint = tensordiag(constraint)
		return constraint

	def reaction_force(self, u):
		 # a nxsxs tensor, where n is the degrees of freedom of the position:
		reaction_force = np.tensordot(self.codistribution(u), self.lag(u), [0,0])
		reaction_force = tensordiag(reaction_force)
		return reaction_force

	def multi_dynamics(self, ut):
		"""
		Split the Lagrange-d'Alembert equations in a Spark LobattoIIIA-B method.
		It splits the vector field into two parts.
		f_1 = [v, 0]
		f_2 = [0, f + F]

		where f is the external force and F is the reaction force stemming from the constraints.
		"""
		v = self.velocity(ut)
		return {
		rk.LobattoIIIA: np.concatenate([v, np.zeros_like(v)]),
		rk.LobattoIIIB: np.concatenate([np.zeros_like(v), self.force(ut) + self.reaction_force(ut)])
		}


class ContactOscillator(NonHolonomic):
	"""
Example 5.2 in [MP]_.

This is the example presented in [MP]_ § 5.2. It is a nonlinear
perturbation of the contact oscillator.


.. [MP] R. McLachlan and M. Perlmutter, *Integrators for Nonholonomic Mechanical Systems*, J. Nonlinear Sci., **16**, No. 4, 283-328., (2006). :doi:`10.1007/s00332-005-0698-1`
	"""

	size = 7 # 3+3+1

	def __init__(self, epsilon=0.):
		self.epsilon = epsilon

	def label(self, component):
		return [u'x',u'y',u'z',u'ẋ',u'ẏ',u'ż',u'λ'][component]

	def position(self, u):
		return u[:3]

	def velocity(self, u):
		return u[3:6]

	def average_velocity(self, u0, u1):
		return (self.velocity(u0) + self.velocity(u1))/2

	def state(self,u):
		return u[:6]

	def lag(self, u):
		return u[6:7]

	def assemble(self, q,v,l):
		return np.hstack([q,v,l])

	def force(self, u):
		q = self.position(u) # copy?
		return -q - self.epsilon*q[2]*q[0]*array([q[2],np.zeros_like(q[0]),q[0]])

	def average_force(self, u0, u1):
		q0, q1 = self.position(u0), self.position(u1)
		x0,z0 = q0[0],q0[2]
		x1,z1 = q1[0],q1[2]
		qm = (q0+q1)/2
		px = (x0*z0**2 + x1*z1**2)/4 + (2*z0*z1*(x0+x1) + x0*z1**2 + x1*z0**2)/12
		pz = (z0*x0**2 + z1*x1**2)/4 + (2*x0*x1*(z0+z1) + z0*x1**2 + z1*x0**2)/12
		return -qm - self.epsilon*array([px, np.zeros_like(q0[0]), pz])

	def codistribution(self, u):
		q = self.position(u)
		return np.array([[np.ones_like(q[1]), np.zeros_like(q[1]), q[1]]])

	def energy(self, u):
		vel = self.velocity(u)
		q = self.position(u)
		return .5*(vel[0]**2 + vel[1]**2 + vel[2]**2 + q[0]**2 + q[1]**2 + q[2]**2 + self.epsilon*q[0]**2*q[2]**2)

	def initial(self, z0, e0=1.5, z0dot=0.):
		q0 = array([np.sqrt( (2*e0 - 2*z0dot**2 - z0**2 - 1) / (1 + self.epsilon*z0**2) ), 1., z0])
		p0 = array([-z0dot, 0, z0dot])
		v0 = p0
		l0 = ( q0[0] + q0[1]*q0[2] - p0[1]*p0[2] + self.epsilon*(q0[0]*q0[2]**2 + q0[0]**2*q0[1]*q0[2] ) ) / ( 1 + q0[1]**2 )
		return np.hstack([q0, v0, l0])

	def time_step(self, N=40):
		return 2*np.sin(np.pi/N)



class VerticalRollingDisk(NonHolonomic):
	"""
	Vertical Rolling Disk
	"""

	size = 10 # 4+4+2

	def __init__(self, mass=1., radius=1., Iflip=1., Irot=1.):
		"""
		:mass: mass of the disk
		:radius: Radius of the disk
		:Iflip: inertia momentum around the "flip" axis
		:Irot: inertia momentum, around the axis of rotation symmetry of the disk (perpendicular to it)
		"""
		self.mass = mass
		self.radius = radius
		self.Iflip = Iflip
		self.Irot = Irot

	def label(self, component):
		return ['x','y',u'φ',u'θ','vx','vy',u'ωφ',u'ωη',u'λ1',u'λ2'][component]

	def position(self, u):
		"""
		Positions x,y,φ (SE(2) coordinates), θ (rotation)
		"""
		return u[:4]

	def velocity(self, u):
		return u[4:8]

	def average_velocity(self, u0, u1):
		return (self.velocity(u0) + self.velocity(u1))/2

	def average_force(self, u0, u1):
		return self.force(u0) # using the fact that the force is zero in this model

	def lag(self,u):
		return u[8:10]

	def codistribution(self, u):
		q = self.position(u)
		phi = q[2]
		R = self.radius
		one = np.ones_like(phi)
		zero = np.zeros_like(phi)
		return np.array([[one, zero, zero, -R*np.cos(phi)],[zero, one, zero, -R*np.sin(phi)]])

	def state(self,u):
		return u[:8]

	def force(self,u):
		return np.zeros_like(self.position(u))

	def assemble(self,q,v,l):
		return np.hstack([q,v,l])

	def qnorm(self, ut):
		return np.sqrt(ut[0]**2 + ut[1]**2)

	def energy(self, ut):
		return .5*(self.mass*(ut[4]**2 + ut[5]**2) + self.Iflip*ut[6]**2 + self.Irot*ut[7]**2)

	def exact(self,t,u0):
		"""
		Exact solution for initial condition u0 at times t

:param array(N) t: time points of size N
:param array(8+) u0: initial condition
:return: a 10xN matrix of the exact solution
		"""
		ohm_phi,ohm_theta = u0[6:8]
		R = self.radius
		rho = ohm_theta*R/ohm_phi
		x_0,y_0,phi_0,theta_0 = u0[:4]
		phi = ohm_phi*t+phi_0
		one = np.ones_like(t)
		m = self.mass
		return np.vstack([rho*(np.sin(phi)-np.sin(phi_0)) + x_0,
					-rho*(np.cos(phi)-np.cos(phi_0)) + y_0,
					ohm_phi*t+phi_0,
					ohm_theta*t+theta_0,
					R*np.cos(phi)*ohm_theta,
					R*np.sin(phi)*ohm_theta,
					ohm_phi*one,
					ohm_theta*one,
					-m*ohm_phi*R*ohm_theta*np.sin(phi),
					m*ohm_phi*R*ohm_theta*np.cos(phi),])

class Exponential(System):
	def __init__(self, nonlin, L):
		self.L = L
		self.nonlin = nonlin

	def linear(self):
		return self.L

	def f(self, t, u):
		return np.dot(self.linear(), u) + self.nonlin(t,u)

def zero_dynamics(t,u):
	return np.zeros_like(u)

class Linear(Exponential):
	def __init__(self, L):
		super(Linear, self).__init__(zero_dynamics, L)

class NoLinear(Exponential):
	def __init__(self, f, size):
		super(NoLinear,self).__init__(f, np.zeros([size,size]))


class Burgers(Exponential):
	def __init__(self, viscosity=0.03, size=128):
		self.viscosity = viscosity
		self.size = size
		self.initialize()

	def linear(self):
		return -self.laplace


class BurgersComplex(Burgers):
	def initialize(self):
		self.k = 2*np.pi*np.array(np.fft.fftfreq(self.size, 1/self.size),dtype='complex')
		self.k[len(self.k)/2] = 0
		self.laplace = self.viscosity*np.diag(self.k**2)
		x = np.linspace(0,1,self.size,endpoint=False)
		self.points = x - x.mean() # too lazy to compute x.mean manually here...

	def preprocess(self, u0):
		return np.fft.fft(u0)

	def postprocess(self, u1):
		return np.real(np.fft.ifft(u1))

	def nonlin(self, t, u):
		return -0.5j * self.k * np.fft.fft(np.real(np.fft.ifft(u)) ** 2)

class OrnsteinUhlenbeck(System):
	def __init__(self, sigma=1, theta=1, mu=1):
		self.sigma = sigma
		self.theta = theta
		self.mu = mu

	def mass(self, t, u):
		return u

	def deterministic(self, t, u):
		return self.theta*(self.mu - u)

	def noise(self, t, u):
		return self.sigma*np.identity(len(u))

class Signal(object):
	pass

class LinBumpSignal(Signal):
	def __init__(self, V0, t0):
		self.t0 = t0
		self.V0 = V0

	def __call__(self, t):
		t0 = self.t0
		V0 = self.V0
		if t < t0:
			return 0.
		if t0 <= t < 2*t0:
			return V0*(t-t0)/t0
		if 2*t0 <= t < 3*t0:
			return V0
		if 3*t0 <= t < 4*t0:
			return -V0*(t-4*t0)/t0
		if 4*t0 <= t:
			return 0

class SineSignal(Signal):
	def __init__(self, V0):
		self.V0 = V0

	def __call__(self, t):
		return self.V0*np.sin(2*np.pi*t/2e-8)


class Differentiator(System):
	kT = 300*1e-23

	def __init__(self, signal, C=1e-12,G=1e-4,A=300.):
		self.signal = signal
		self.C = C
		self.G = G
		self.A = A
		self.mass_mat = np.zeros([5,5])
		self.mass_mat[:2,:2] = np.array([[C,-C],[-C,C]])
		self.det_mat = np.zeros([5,5])
		self.det_mat[1:3,1:3] = np.array([[G,-G],[-G,G]])
		self.det_mat[0,3] = 1.
		self.det_mat[2,-1] = -1
		self.det_mat[3,1:3] = np.array([A,1])
		self.det_mat[-1,0] = 1.
		self.det_mat *= -1

	def mass(self,t,u):
		return np.dot(self.mass_mat,u)


	def V(self,t):
		V = np.zeros(5)
		V[-1] = self.signal(t)
		return V


	def deterministic(self, t, u):
		return np.dot(self.det_mat, u) + self.V(t)

	def noise(self, t, u):
		return np.sqrt(4*self.kT*self.G)*np.array([0,1.,-1,0,0]).reshape(-1,1)


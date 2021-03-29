import time
from fractions import Fraction
import os,sys
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from programs.engine.discrete_gaussian_utility import RationalSimpleDiscreteLaplace, RationalSimpleDiscreteGaussian
from programs.engine.rngs import DASRandom, DASRandomBuffered
from programs.engine.tests.test_eps_delta_utility import SimpleDiscreteGaussian as FloatDiscreteGaussian # TODO: remove this? Uses copious float-ops; but, its speed is useful for large-scale experiments
from programs.engine.primitives import RationalDiscreteGaussianMechanism

# N = 1000
# t0 = time.time()
# for s in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]:
#     RationalSimpleDiscreteLaplace(s=s, t=8, size=N, rng=DASRandom())
# print(f"{N} DiscreteLaplace time: {time.time() - t0}")
#
# t0 = time.time()
# for s in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]:
#     RationalSimpleDiscreteGaussian(sigma_sq=Fraction(1, s), size=N, rng=DASRandom())
# print(f"{N} DiscreteGaussian time: {time.time() - t0}")

N = 10000
t0 = time.time()
RationalSimpleDiscreteLaplace(s=10, t=1 * 2, size=N, rng=DASRandom())
print(f"{N} DiscreteLaplace DASRandom time: {time.time() - t0}")

t0 = time.time()
RationalSimpleDiscreteGaussian(sigma_sq=Fraction(1, 20), size=N, rng=DASRandom())
#RationalDiscreteGaussianMechanism(inverse_scale=Fraction(1, 1 << 40), true_answer=np.zeros(N))
print(f"{N} DiscreteGaussian DASRandom time: {time.time() - t0}")

t0 = time.time()
RationalSimpleDiscreteLaplace(s=10, t=1 * 2, size=N, rng=DASRandomBuffered())
print(f"{N} DiscreteLaplace DASRandomLemire time: {time.time() - t0}")

t0 = time.time()
RationalSimpleDiscreteGaussian(sigma_sq=Fraction(1, 20), size=N, rng=DASRandomBuffered())
print(f"{N} DiscreteGaussian DASRandomLemire time: {time.time() - t0}")

t0 = time.time()
FloatDiscreteGaussian(variance=float(Fraction(1, 20)), size=N, rng=DASRandom())
print(f"{N} FloatDiscreteGaussian DASRandom time: {time.time() - t0}")

#t0 = time.time()
#FloatDiscreteGaussian(variance=float(Fraction(1, 20)), size=N, rng=DASRandomBuffered())
#print(f"{N} DiscreteGaussian DASLemire time: {time.time() - t0}")

t0 = time.time()
sensitivity = 2
epsilon = float(Fraction(20, 1))
p = 1 - np.exp(-epsilon / float(sensitivity))
rng = DASRandom()
x = rng.geometric(p, size=N) - 1  # numpy geometrics start with 1
y = rng.geometric(p, size=N) - 1
protected_answer = x - y
print(f"{N} OriginalGeometricMechanism DASRandom time: {time.time() - t0}")

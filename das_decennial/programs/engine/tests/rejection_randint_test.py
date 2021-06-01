import pytest
import numpy as np

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from programs.engine.rngs import DASRDRandIntegers


@pytest.fixture
def rng():
    return DASRDRandIntegers()


@pytest.mark.parametrize("nbits, nint64", [
    (3, 1),
    (63, 1),
    (64, 2),
    (125, 2),
    (127, 2),
    (128, 3),
])
def test_nextint(rng, nbits, nint64):
    bl = rng._nextint(nbits // 64 + 1).bit_length()
    assert bl <= 64 * nint64
    assert 64 * nint64 // bl == 1


@pytest.mark.parametrize("a, b", [
    (1234132, 2345252345),
    (0, 3),
    (0, 1 << 20),
    (0, 1 << 30),
    (0, (1 << 30) + 247852475),
    (0, (1 << 63)),
    (0, (1 << 62) + 130091709234),
    (0, (1 << 63) + 1),
    (0, (1 << 64) + 1),
    (0, (1 << 64) - 1 ),
    (0, (1 << 64) + 1),
    (123213, (1 << 64) + 2143053948),
    (123213, (1 << 85) + 2143053948),
    (-123213, (1 << 64) + 2143053948),
    (123213, -(1 << 85) + 2143053948),
])
def test_integers(rng, a, b):
    alg = DASRDRandIntegers()
    N = 10000
    n = b - a
    if a > b:
        with pytest.raises(ValueError, match="Interval length is not positive"):
            alg.integers(low=a, high=b)
        return
    draws = [alg.integers(low=a, high=b) for _ in range(N)]
    assert sum([d >= a for d in draws]) == N
    assert sum([d < b for d in draws]) == N
    if n > 100000:
        # Most significant bit returns 0s and 1s with prob 1/2. variance is p(1-p)/N = 1 / 4N
        assert (sum([d >= (a + n // 2) for d in draws]) / N - 0.5) ** 2 < 4. / N  # 4 stdev => 16 var
        assert (sum([d < (a + n // 2) for d in draws]) / N - 0.5)  ** 2 < 4. / N  # 4 stdev => 16 var
        # Least significant bit returns 0s and 1s with prob 1/2. variance is p(1-p)/N = 1 / 4N
        assert (sum([d % 2 for d in draws]) / N - 0.5) ** 2 < 4. / N  # 4 std => 16 var
    m = float(sum(draws)) / N
    # print((m - (a + b -1) / 2) ** 2, 4 * (n * n - 1.) / N)
    assert (m - (a + b - 1) / 2) ** 2 < 4 * (n * n - 1.) / N


@pytest.mark.parametrize("a", [
    0, 1, 2, 10, 100, 1000, 1 << 64, 1 << 80
])
def test_integers_0123(rng, a):
    alg = DASRDRandIntegers()
    N = 10000
    # rangelen = 0
    with pytest.raises(ValueError, match="Interval length is not positive"):
        float(sum([alg.integers(low=a, high=a) for _ in range(N)])) / N

    # rangelen = 1
    draws = [alg.integers(low=a, high=a + 1) for _ in range(N)]
    assert sum([d == a for d in draws]) == N

    # rangelen = 2
    draws = [alg.integers(low=a, high=a + 2) for _ in range(N)]
    assert (sum([d == a for d in draws]) / N - 0.5) ** 2 < 4. / N
    assert (sum([d == a + 1 for d in draws]) / N - 0.5) ** 2 < 4. / N

    # rangelen = 3
    # variance is p(1-p)/N = 1 / 3 * 2/3 / N = 2/9N
    draws = [alg.integers(low=a, high=a + 3) for _ in range(N)]
    assert (sum([d == a for d in draws]) / N - 1./3.) ** 2 < 16 * 2./9./N
    assert (sum([d == a + 1 for d in draws]) / N - 1./3.) ** 2 < 16 * 2./9./N
    assert (sum([d == a + 2 for d in draws]) / N - 1. / 3.) ** 2 < 16 * 2./9./N


@pytest.mark.parametrize("a, b", [
    (1, 6),
    (10, 16),
    (10, 74),
    (0, 100),
    (0, 1000),
])
def test_integers_small(rng, a, b):
    """ Seeing each number is drawn equal number of times. Multinomial distribution."""
    alg = DASRDRandIntegers()
    N = 100000
    n = b - a
    p = 1. / n
    h = np.zeros(n, dtype=int)
    for _ in range(N):
        h[(alg.integers(low=a, high=b) - a)] +=1
    # print(abs(h - N / n), 4. *  np.sqrt(N * p * (1. - p)))
    assert np.all(abs(h - N / n) < 4. *  np.sqrt(N * p * (1. - p)))

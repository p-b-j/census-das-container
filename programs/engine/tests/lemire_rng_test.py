import time
from collections import Counter
import numpy as np
from programs.engine.rngs import DASRandomBuffered


if __name__ == "__main__":
    ## This test does not work by itself. This is meant to see if there is bias, with L=3 set in the Lemire routine
    rng = DASRandomBuffered()
    N = 10000
    ll = []
    for run in range(100):
        t0 = time.time()
        ints = [rng.integers(0, 7) for _ in range(N)]
        #print(f"{N} np int time: {time.time() - t0}")
        c = Counter(ints)
        mean = np.mean(list(c.values()))
        devdict = {k: v - mean for k,v in c.items()}
        devdict = {k: devdict[k] for k in sorted(devdict)}
        ll.append(np.array(list(devdict.values())))
    allruns = np.array(ll)
    print(allruns)
    print(allruns.mean(axis=0))
    print(np.sqrt(allruns.var(axis=0)))
    # print(ints)
    # h = np.histogram(ints, bins=8, range=(0,7))
    # print(h)
    # print(100 * h[0] / np.average(h[0]) - 100)
    # print(np.std(h[0])/np.average(h[0]))
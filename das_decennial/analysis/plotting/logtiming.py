import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas
import numpy


def algsetOrder(algsets):
    algsets = numpy.unique(algsets)
    algsets = [x[:3] + "." + x[3:] if x[2] == "0" else x for x in algsets]
    algsets.sort(key=lambda s: float(s[2:]))
    algsets = [x[:3] + x[4:] if "." in x else x for x in algsets]
    return algsets


def algsetToFloat(algset):
    return float(algset[2:3] + "." + algset[3:]) if algset[2] == "0" else float(algset[2:])


def getTimingDF(logfile):
    with open(logfile, "r") as f:
        contents = f.readlines()
    times = [x.split(" | ") for x in contents if "--ENGINE" in x]
    df = pandas.DataFrame(times)
    df.columns = ["Timer Type", "Time Start", "Time End", "Elapsed Time", "Algset", "Trial"]
    df["Trial"] = [x.split("\n")[0] for x in df["Trial"]]
    df = df.drop(["Timer Type", "Time Start", "Time End"], axis=1)
    df['Elapsed Time'] = df['Elapsed Time'].astype("float")
    df['Algset'] = pandas.Categorical(df['Algset'], algsetOrder(df['Algset']))
    return df



#logfile = "/mnt/users/moran331/das_decennial/logs/topdown_az04_PLB_time.out"
#logfile = "/mnt/users/moran331/das_decennial/logs/topdown_ri44_PLB_time.out"
#logfile = "/mnt/users/moran331/gits/das_decennial/logs/topdown_ca06_PLB_time.out"
logfile = "/mnt/users/moran331/important_logs/topdown_az04_timing/topdown_az04_PLB_time.out"
df = getTimingDF(logfile)

df['PLB'] = [algsetToFloat(x) for x in df['Algset']]

desc = df.groupby("PLB").describe()


desc = desc.drop("count", axis=1, level=1)
desc = desc.drop("std", axis=1, level=1)
#desc = desc.drop(("Elapsed Time", "25%"), axis=1)
#desc = desc.drop(("Elapsed Time", "75%"), axis=1)

state = "California"
title = f"Engine Run Times for {state} on the PL94 CVAP Schema (25 Runs per PLB)"

# round to the nearest hundred
# min = desc.min().min().round(-2)
# min = 0 if (min-100) < 0 else (min-100)
min = 0
max = desc.max().max().round(-2)

#ax = desc.plot(ylim=(min,max), style=".-", fontsize=6, logx=True, alpha=0.75)
ax = desc.plot(ylim=(min,max), style=".-", fontsize=6, logx=False, alpha=0.75)
# ax.set_xticks(desc.index.tolist())
# ax.set_xticklabels(desc.index.tolist())
ax.set_ylabel("Elapsed Time (seconds)", fontsize=7)
ax.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
ax.legend(loc='lower center', ncol=3, frameon=False, fontsize=6)
ax.set_title(title, {"fontsize":8})

#df.groupby("Algset").mean().plot(style=".-")

#desc.T.plot(kind="box")


plt.savefig("/mnt/users/moran331/other/az04_pl94_cvap_engine_times_no_logx.pdf")
#plt.savefig("/mnt/users/moran331/other/ri44_pl94_cvap_engine_times.pdf")
#plt.savefig("/mnt/users/moran331/other/ca06_pl94_cvap_engine_times_without_first_run.pdf")



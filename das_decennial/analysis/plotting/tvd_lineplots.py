

import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas
import numpy

tvdcsv = "/mnt/users/moran331/jason/pl94_cvap_experiment_detailed_accuracy.csv"
df = pandas.read_csv(tvdcsv)
state = ""
title = f"{state} PL94 CVAP Schema (25 Runs per PLB)"

min = -0.3
max = 1.01

title = "Accuracy as a Fxn of Privacy-Loss Budget, Geolevel\n(Data Product: PL94-CVAP)"
fig, ax = plt.subplots()
mean = df.groupby(['plb', "geolevel"], as_index=False).mean()
for label, group in mean.groupby("geolevel"):
    plot = group.plot(x='plb',
                      y='1-tvd',
                      ylim=(min, max),
                      style=".-",
                      fontsize=6,
                      alpha=0.75,
                      ax=ax,
                      xlim=(-5, 105),
                      markersize=4,
                      label=label)
    #plot.set_xticks(group.plb)
    #plot.set_xticklabels(group.plb)
    plot.set_ylabel("1-TVD", fontsize=7)
    plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
    ax.set_title(title, {"fontsize":8})

plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=4)

plt.savefig("/mnt/users/moran331/jason/pl94_cvap_experiment_detailed_accuracy.pdf")


title = "Accuracy as a Fxn of Privacy-Loss Budget, Geolevel\n(Data Product: PL94-CVAP)"
fig, ax = plt.subplots()
mean = df.groupby(['plb', "geolevel"], as_index=False).mean()
for label, group in mean.groupby("geolevel"):
    plot = group.plot(x='plb',
                      y='1-tvd',
                      ylim=(min, max),
                      style=".-",
                      fontsize=6,
                      alpha=0.75,
                      ax=ax,
                      logx=True,
                      xlim=(-5, 105),
                      markersize=4,
                      label=label)
    plot.set_xticks(group.plb)
    plot.set_xticklabels(group.plb)
    plot.set_ylabel("1-TVD", fontsize=7)
    plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
    ax.set_title(title, {"fontsize":8})

plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=4)

plt.savefig("/mnt/users/moran331/jason/pl94_cvap_experiment_detailed_accuracy_logx.pdf")




#ax = set_xticks(mean.index

#min = mean.min().min().round(1)
#max = 1.01

# fig, ax = plt.subplots()
# meanplot = df.groupby('geolevel').plot(
#     x='plb',
#     y='1-tvd', 
#     ax=ax, 
#     ylim=(min, max), 
#     xlim=(-5, 105),
#     style='.-', 
#     fontsize=6, 
#     #logx=True, 
#     alpha=0.55
# )



#meanplot.set_xticks(mean.index.tolist())
#mean.set_xticklabels(mean.index.tolist())
#mean.set_ylabel("1-TVD", fontsize=7)
#mean.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
#mean.legend(loc='lower right', ncol=2, frameon=False, fontsize=6)
#mean.set_title(title, {"fontsize":8})






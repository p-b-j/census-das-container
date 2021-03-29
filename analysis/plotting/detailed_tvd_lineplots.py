

import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rc
import pandas
import numpy

# https://stackoverflow.com/questions/8376335/styling-part-of-label-in-legend-in-matplotlib
# activate latex text rendering
# rc('text', usetex=True)


if __name__ == "__main__":
    tvdcsv = "/mnt/users/moran331/jason/pl94_cvap_experiment_detailed_accuracy.csv"
    df = pandas.read_csv(tvdcsv)
    geolevels = ['National', 'State', 'County', 'Tract', 'Block_Group', 'Block', 'SLDU', 'SLDL']
    #geolevels.reverse()
    df.geolevel = pandas.Categorical(df.geolevel, categories=geolevels)
    df = df.sort_values(['plb', 'run_id', 'geolevel'])
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
                          alpha=0.85,
                          ax=ax,
                          xlim=(-5, 105),
                          markersize=3,
                          linewidth=1.0,
                          label=label)
        #plot.set_xticks(group.plb)
        #plot.set_xticklabels(group.plb)
        plot.set_ylabel("1-TVD", fontsize=7)
        plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
        ax.set_title(title, {"fontsize":8})
        
    legend = plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=4, title="Geolevels")        
    legend.get_title().set_fontsize(7)
    plt.savefig("/mnt/users/moran331/jason/pl94_cvap_experiment_detailed_accuracy.pdf")


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
                          alpha=0.85,
                          ax=ax,
                          logx=True,
                          xlim=(-5, 105),
                          markersize=3,
                          linewidth=1.0,
                          label=label)
        plot.set_xticks(group.plb)
        plot.set_xticklabels(group.plb)
        plot.set_ylabel("1-TVD", fontsize=7)
        plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
        ax.set_title(title, {"fontsize":8})
            
    legend = plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=4, title="Geolevels")
    legend.get_title().set_fontsize(7)
    plt.savefig("/mnt/users/moran331/jason/pl94_cvap_experiment_detailed_accuracy_logx.pdf")

    
    min = 0.49
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
                          alpha=0.85,
                          ax=ax,
                          xlim=(-5, 105),
                          markersize=3,
                          linewidth=1.0,
                          label=label)
        plot.set_ylabel("1-TVD", fontsize=7)
        plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
        ax.set_title(title, {"fontsize":8})
            
    legend = plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=4, title="Geolevels")
    legend.get_title().set_fontsize(7)
    plt.savefig("/mnt/users/moran331/jason/pl94_cvap_experiment_detailed_accuracy_50percent_cutoff.pdf")



    min = 0.74
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
                          alpha=0.85,
                          ax=ax,
                          xlim=(-5, 105),
                          markersize=3,
                          linewidth=1.0,
                          label=label)
        plot.set_ylabel("1-TVD", fontsize=7)
        plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
        ax.set_title(title, {"fontsize":8})
            
    legend = plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=4, title="Geolevels")
    legend.get_title().set_fontsize(7)
    plt.savefig("/mnt/users/moran331/jason/pl94_cvap_experiment_detailed_accuracy_75percent_cutoff.pdf")



    
    min = 0.49
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
                          alpha=0.85,
                          ax=ax,
                          xlim=(-1, 17),
                          markersize=3,
                          linewidth=1.0,
                          label=label)
        plot.set_ylabel("1-TVD", fontsize=7)
        plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
        ax.set_title(title, {"fontsize":8})
            
    legend = plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=4, title="Geolevels")
    legend.get_title().set_fontsize(7)
    plt.savefig("/mnt/users/moran331/jason/pl94_cvap_experiment_detailed_accuracy_zoomed_to_PLB16.pdf")

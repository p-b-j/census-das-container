

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
    jason = "/mnt/users/moran331/jason/"
    query_acc = "query_accuracy/"
    plot_dir = "plots/"
    tvdcsv = f"{jason}{query_acc}pl94_cvap_experiment_query_accuracy_allPLBs.csv"
    save_dir = f"{jason}{query_acc}{plot_dir}"
    df = pandas.read_csv(tvdcsv)
    geolevels = ['National', 'State', 'County', 'Tract', 'Block_Group', 'Block', 'SLDU', 'SLDL']
    #geolevels.reverse()
    df.geolevel = pandas.Categorical(df.geolevel, categories=geolevels)
    df = df.sort_values(['plb', 'run_id', 'geolevel'])
    # the query accuracy values were saved with the unnamed index column, so remove it
    df = df[df.columns[1:]]
    # since we have 3 different queries in this data, we'll be using a loop to do the heavy lifting
    maindf = df
    queries = maindf['query'].unique()
    query_titles = {
        'citizen * votingage': "Citizen x Voting Age Sub-Histogram", 
        'hhgq'               : "Household and Group Quarters Sub-Histogram",
        'cenrace * hispanic' : "Cenrace x Hispanic Sub-Histogram"
    }
    for query in queries:
        df = maindf[maindf['query'] == query]
        queryfs = ".".join(query.split(" * "))
        min = -0.2
        max = 1.01
        title = f"Accuracy as a Fxn of Privacy-Loss Budget, Geolevel\n{query_titles[query]}\n(Data Product: PL94-CVAP)"
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
        save_name = f"pl94_cvap_experiment_{queryfs}_accuracy.pdf"
        saveloc = f"{save_dir}{save_name}"
        plt.savefig(saveloc)


        min = -0.2
        max = 1.01
        title = f"Accuracy as a Fxn of Privacy-Loss Budget, Geolevel\n{query_titles[query]}\n(Data Product: PL94-CVAP)"
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
        save_name = f"pl94_cvap_experiment_{queryfs}_accuracy_logx.pdf"
        saveloc = f"{save_dir}{save_name}"
        plt.savefig(saveloc)

    

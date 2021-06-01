

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
    query_acc = "sparsity_diff_quantiles/"
    plot_dir = "plots/"
    tvdcsv = f"{jason}{query_acc}sparsityDiffQuantiles.csv"
    save_dir = f"{jason}{query_acc}{plot_dir}"
    df = pandas.read_csv(tvdcsv)
    geolevels = ['National', 'State', 'County', 'Tract', 'Block_Group', 'Block', 'SLDU', 'SLDL']
    #geolevels.reverse()
    df.geolevel = pandas.Categorical(df.geolevel, categories=geolevels)
    df = df.sort_values(['plb', 'geolevel'])
    
    # dflong = pandas.wide_to_long(df, stubnames='q', i=['plb', 'geolevel'], j='metric', sep="")
    # print(dflong)
    dfmelt = pandas.melt(df, 
                         id_vars=['plb', 'geolevel'], 
                         value_vars=[f"q{x}" for x in range(11)], 
                         var_name="quantile", 
                         value_name="metric")
    print(dfmelt)
    geolevels1 = {    
        "National": "#a6cee3",
        #"State" : "#1f78b4",
        #"County": "#b2df8a",
        "Tract": "#33a02c",
        #"Block_Group": "#fb9a99",
        "Block": "#e31a1c",
        #"SLDL": "#fdbf6f",
        #"SLDU": "#ff7f00"
    }

    geolevels2 = {
        "National"   : "#66c2a5",
        #"State"      : "#fc8d62",
        #"County"     : "#8da0cb",
        "Tract"      : "#e78ac3", 
        #"Block_Group": "#a6d854",
        "Block"      : "#ffd92f",
        #"SLDL"       : "#e5c494",
        #"SLDU"       : "#b3b3b3"
    }
    selected_geolevels = geolevels1
    legend_handlers = []
    save_name = f"pl94_cvap_experiment_sparsity_diff_quantiles"
    fig, ax = plt.subplots()
    for label, group in dfmelt.groupby(["geolevel", "quantile"]):
        print(label)
        print(group)
        x = "plb"
        y = "metric"
        style = ".-"
        alpha = 0.25
        xlim = (-0.25, 16.25)
        linewidth = 1.0
        markersize = 1
        legend = False
        legend_label = '_nolegend_'
        color = "#cccccc"
        logy = False
        title = "L1 NNZ Difference as a Fxn of PLB, Geolevel\n(Data Product: PL94-CVAP)"
        xlabel = "Privacy Loss Budget (PLB)"
        ylabel = "L1 NNZ Difference"
        if logy:
            if "_logy" not in save_name:
                save_name = f"{save_name}_logy"
        if style == ".":
            if "_dot_only" not in save_name:
                save_name = f"{save_name}_dot_only"
        if label[0] in selected_geolevels:
            color = selected_geolevels[label[0]]
            alpha = 0.50
            legend_geolevels = [x[0] for x in legend_handlers]
            if label[0] not in legend_geolevels:
                legend_handlers.append(label)
                legend=True
                legend_label = label[0]
        plot = group.plot(x=x,
                          y=y,
                          ax=ax,
                          style=style,
                          alpha=alpha,
                          xlim=xlim,
                          linewidth=linewidth,
                          markersize=markersize,
                          legend=legend,
                          logy=logy,
                          color=color,
                          label=legend_label
        )
        ax.set_title(title, {"fontsize": 8})
        plot.set_xlabel(xlabel, fontsize=7)
        plot.set_ylabel(ylabel, fontsize=7)
        plot.tick_params(axis='both', which='major', labelsize=6)

    print(legend_handlers)                                   
    legend = plt.legend(loc='upper right', frameon=False, fontsize=6, ncol=4, title="Geolevels")
    legend.get_title().set_fontsize(7)
    saveloc = f"{save_dir}{save_name}.pdf"
    plt.savefig(saveloc)





    # min = -0.2
    # max = 1.01
    # title = f"Sparsity Metric as a Fxn of Privacy-Loss Budget, Geolevel\n(Data Product: PL94-CVAP)"
    # fig, ax = plt.subplots()
    # mean = df.groupby(['plb', "geolevel"], as_index=False).mean()
    # for label, group in mean.groupby("geolevel"):
    #     plot = group.plot(x='plb',
    #                       y='1-tvd',
    #                       ylim=(min, max),
    #                       style=".-",
    #                       fontsize=6,
    #                       alpha=0.85,
    #                       ax=ax,
    #                       xlim=(-5, 105),
    #                       markersize=3,
    #                       linewidth=1.0,
    #                       label=label)
    #     #plot.set_xticks(group.plb)
    #     #plot.set_xticklabels(group.plb)
    #     plot.set_ylabel("L1(Priv_nz - Orig_nz)", fontsize=7)
    #     plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
    #     ax.set_title(title, {"fontsize":8})
        
    # legend = plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=4, title="Geolevels")        
    # legend.get_title().set_fontsize(7)
    # save_name = f"pl94_cvap_experiment_sparsity_diff_quantiles.pdf"
    # saveloc = f"{save_dir}{save_name}"
    # plt.savefig(saveloc)
    

    # min = -0.2
    # max = 1.01
    # title = f"Sparsity Metric as a Fxn of Privacy-Loss Budget, Geolevel\n(Data Product: PL94-CVAP)"
    # fig, ax = plt.subplots()
    # mean = df.groupby(['plb', "geolevel"], as_index=False).mean()
    # for label, group in mean.groupby("geolevel"):
    #     plot = group.plot(x='plb',
    #                       y='1-tvd',
    #                       ylim=(min, max),
    #                       style=".-",
    #                       fontsize=6,
    #                       alpha=0.85,
    #                       ax=ax,
    #                       logx=True,
    #                       xlim=(-5, 105),
    #                       markersize=3,
    #                       linewidth=1.0,
    #                       label=label)
    #     plot.set_xticks(group.plb)
    #     plot.set_xticklabels(group.plb)
    #     plot.set_ylabel("L1(Priv_nz - Orig_nz)", fontsize=7)
    #     plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
    #     ax.set_title(title, {"fontsize":8})
            
    # legend = plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=4, title="Geolevels")
    # legend.get_title().set_fontsize(7)
    # save_name = f"pl94_cvap_experiment_sparsity_diff_quantiles_logx.pdf"
    # saveloc = f"{save_dir}{save_name}"
    # plt.savefig(saveloc)

    

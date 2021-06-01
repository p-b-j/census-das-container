import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rc
import pandas
import numpy

if __name__ == "__main__":
    ### Things to enter manually
    #tvdcsv = "/mnt/users/moran331/products/PL94_P12/RI_detailed_query_accuracy.csv"
    #tvdcsv = "/mnt/users/lecle301/products/DHCP_HHGQ/NM_cenrace_x_Hisp_td01_to_td8_query_accuracy.csv"
    tvdcsv = "/mnt/users/lecle301/products/Household2010/NM_TotalOnly_td01_to_td8_query_accuracy.csv"
    schema_name = "Household2010"
    state = "New Mexico"
    plot_saveloc = f"/mnt/users/lecle301/products/{schema_name}/NM_TotalOnly_td01_to_td8_query_accuracy.pdf"

    # Things that can be changed if needed
    min = -0.1
    max = 1.01
    xlim = (0.0, 8.25)
    data_product_name = "DHC-H"
    title = f"Statistic: Total Population Only\nAccuracy as a Fxn of Privacy-Loss Budget (for {state}), Geolevel\n(Data Product: {data_product_name})"

    df = pandas.read_csv(tvdcsv)
    geolevels = ['State', 'County', 'Tract_Group', 'Tract', 'Block_Group', 'Block']
    df.geolevel = pandas.Categorical(df.geolevel, categories=geolevels)
    df = df.sort_values(['plb', 'run_id', 'geolevel'])

    fig, ax = plt.subplots()
    # averages across runs, grouping by PLB and Geolevel
    mean = df.groupby(['plb', "geolevel"], as_index=False).mean()
    for label, group in mean.groupby("geolevel"):
        plot = group.plot(x='plb',
                          y='1-tvd',
                          ylim=(min, max),
                          style=".-",
                          fontsize=6,
                          alpha=0.85,
                          ax=ax,
                          xlim=xlim,
                          markersize=3,
                          linewidth=1.0,
                          label=label)
        plot.set_ylabel("1-TVD", fontsize=7)
        plot.set_xlabel("Privacy Loss Budget (PLB)", fontsize=7)
        ax.set_title(title, {"fontsize":8})
        
    legend = plt.legend(loc='lower right', frameon=False, fontsize=6, ncol=3, title="Geolevels")        
    legend.get_title().set_fontsize(7)
    plt.savefig(plot_saveloc)

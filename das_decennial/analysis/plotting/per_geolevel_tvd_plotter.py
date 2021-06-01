import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rc
import pandas
import numpy
from pathlib import Path

# https://stackoverflow.com/questions/8376335/styling-part-of-label-in-legend-in-matplotlib
# activate latex text rendering
# rc('text', usetex=True)

# csvFile expected format:
#   /mnt/users/lecle301/analyses/cenrace * hispanic/VA_danVariant1_3Trial_allPLBs/per_geolevel_tvd_THIEVISH_WEATHER_2019-10-22_1093_Title_13/cenrace * hispanic/VA_danVariant1_3Trial_allPLBs/Metric_0001.csv
# break it up like:
#   >>> "/mnt/users/lecle301/analyses/cenrace * hispanic/VA_danVariant1_3Trial_allPLBs/per_geolevel_tvd_THIEVISH_WEATHER_2019-10-22_1093_Title_13/cenrace * hispanic/VA_danVariant1_3Trial_allPLBs/Metric_0001.csv".split("/")[4]
#   'analyses'
#   >>> "/mnt/users/lecle301/analyses/cenrace * hispanic/VA_danVariant1_3Trial_allPLBs/per_geolevel_tvd_THIEVISH_WEATHER_2019-10-22_1093_Title_13/cenrace * hispanic/VA_danVariant1_3Trial_allPLBs/Metric_0001.csv".split("/")[5]
#   'cenrace * hispanic'
def getPlotSaveLoc(csvFile):
    splitDirs = csvFile.split('/')
    return '/'.join(splitDirs[:5+1])

def getQueryName(csvFile):
    return csvFile.split('/')[5]

def getExperimentName(csvFile):
    return csvFile.split('/')[6]

#geolevels options: ['National', 'State', 'County', 'Tract', 'Block_Group', 'Block', 'SLDU', 'SLDL']
def plot(csvFile="", geolevels = ['National', 'State', 'County', 'Tract', 'Block_Group', 'Block'], product="DHC-P", state="VA"):
    assert csvFile != "", "Plot cannot accept empty csvFile path."
    df = pandas.read_csv(csvFile)
    print(f"\n---------------------------\nStarting plot work on csvFile:\n{csvFile}")
    print("Read csv as pandas df:")
    print(df)
    print("It has data types:")
    print(df.dtypes)

    query = getQueryName(csvFile)

    df.geolevel = pandas.Categorical(df.geolevel, categories=geolevels)
    df = df.sort_values(['plb', 'run_id', 'geolevel'])

    min = 0.0
    max = 1.01
    title = f"Statistic: {query}\nAccuracy as a Fxn of Privacy-Loss Budget (for {state}), Geolevel\n(Data Product: {product})"
    fig, ax = plt.subplots()
    mean = df.groupby(['plb', "geolevel"], as_index=False).mean()
    for label, group in mean.groupby("geolevel"):
        plot = group.plot(x='plb',
                          y='1-TVD',
                          ylim=(min, max),
                          style=".-",
                          fontsize=6,
                          alpha=0.85,
                          ax=ax,
                          xlim=(0, 16.5),
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
    
    # NOTE: !!!! This assumes there's just one Analysis mission name per query * experiment combination. !!!!
    pltSaveLoc = getPlotSaveLoc(csvFile) + '/' + getExperimentName(csvFile) + "_" + query + ".pdf"
    plt.savefig(pltSaveLoc)

def makeAllPlots(analysisPath="", geolevels=[], product="DHC-P", state="VA"):
    assert geolevels != [], "Geolevels must be non-empty."
    assert analysisPath != "", "Source analysisPath for csvs cannot be empty."
    csvFiles = Path(analysisPath).rglob("*.csv")
    for csvFile in csvFiles:
        csvFile = str(csvFile)
        plot(csvFile=csvFile, geolevels=geolevels, product=product, state=state)

if __name__ == "__main__":
    analysisPath = "/mnt/users/moran331/PL94_P12_Geolevel_TVD/"
    geolevels = ['Nation', 'State', 'County', 'Tract_Group', 'Tract', 'Block_Group', 'Block', 'SLDU', 'SLDL', 'CD']
    product = "PL94_P12" # Extraction from csvFile name not yet automated
    state = "RI" # Extraction from csvFile name not yet automated
    makeAllPlots(analysisPath=analysisPath, geolevels=geolevels, product=product, state=state)







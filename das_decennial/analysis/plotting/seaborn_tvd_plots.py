import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas
import seaborn as sns

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


if __name__ == "__main__":
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("--data", help="csv file with the analysis results data")
    parser.add_argument("--saveloc", help="where to save images")
    args = parser.parse_args()
    
    data = args.data
    data = pandas.read_csv(data)
    print(data)
    geolevels = [
        'NATION',
        'STATE',
        'TRACT_GROUP',
        'TRACT',
        'BLOCK_GROUP',
        'BLOCK',
        'CD',
        'SLDU',
        'SLDL',
    ]
    data.geolevel = pandas.Categorical(data.geolevel, geolevels, ordered=True)
    
    queries = data['query'].unique()
    for query in queries:
        data2 = data[data['query'].isin([query])]
        print(data2)
        columns = ['geolevel', 'plb', 'run_id', '1-TVD']
        data2 = data2[columns]
        data2 = data2.sort_values(['geolevel'])
        data2 = data2.groupby(['geolevel', 'plb'], as_index=False).mean()
        print(data2)
        data3 = data2.pivot(index="geolevel", columns="plb", values="1-TVD")
        print(data3)

        sns.set(font_scale=0.4)
        fig, ax = plt.subplots()
        title = f"Avg_over_runs(Avg_over_geounits(1-TVD)) for query '{query}'"
        plt.title(title, fontsize=6)
        
        snsplot = sns.heatmap(data3, annot=True, linewidths=0.5, ax=ax, cbar=False, vmin=0.0, vmax=1.0, cmap="Blues")
        
        plot = snsplot.get_figure()
        #plot = snsplot
        
        saveloc = args.saveloc
        path, ext = saveloc.split(".")
        saveloc = f"{path}_{query}.{ext}"
        print(saveloc)
        plot.savefig(saveloc)
        plt.clf()

    


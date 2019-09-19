import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from density_plot import density_scatter
from tqdm import tqdm

def draw_graph(title,lower,higher,xD,yD,filename,months=False):
    if type(xD) is list: 
        xD = {'data' : xD }
        yD = {'data' : yD }

    ### General style options
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = 'Ubuntu'
    plt.rcParams['font.monospace'] = 'Ubuntu Mono'
    plt.rcParams['font.size'] = 24
    plt.rcParams['axes.labelsize'] = 24
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['axes.titlesize'] = 24
    plt.rcParams['xtick.major.size'] = 15
    #plt.rcParams['xtick.major.width'] = 20
    plt.rcParams['xtick.minor.size'] = 7.5
    plt.rcParams['xtick.labelsize'] = 24
    plt.rcParams['ytick.labelsize'] = 24
    plt.rcParams['legend.fontsize'] = 24
    plt.rcParams['figure.titlesize'] = 24

    xD = {k:v for (k,v) in xD.items() if len(v) > 100}
    yD = {k:v for (k,v) in yD.items() if len(v) > 100}

    if len(xD.keys()) < 1:
        return
    ### Setup graph
    fig, ax = plt.subplots(len(xD.keys()),1,figsize=(36,24),sharex=True)
    if len(xD.keys()) == 1: 
        ax = [ax]

    #fig.suptitle(title) Disabled for now 
    ax[-1].set_xlabel("Date (Years, Months)")
    ax[-1].set_ylabel("Latency (Seconds)")
    #TODO How to share? 


    ### Setup axes 
    years = mdates.YearLocator()   
    months = mdates.MonthLocator()  

    years_fmt = mdates.DateFormatter('%Y')
    month_fmt = mdates.DateFormatter('%m')

    ax[0].xaxis.set_major_locator(years)
    ax[0].xaxis.set_major_formatter(years_fmt)
    ax[0].xaxis.set_minor_locator(months)
    #ax[0].grid(b=True, which='major',axis='x', color='green', linestyle='-')
    if months:
        ax[0].xaxis.set_minor_formatter(month_fmt)
    #ax[0].set_xlim([min(xD.items(),key=lambda x:x[1]),
                    #max(xD.items(),key=lambda x:x[1])])

    i = 0
    for source in tqdm(yD.keys(),desc='Drawing Heatmaps'):
        ax[i].set_ylim([float(lower),float(higher)])
        x = np.array(xD[source])
        y = np.array(yD[source])
        density_scatter(x,y,bins=1024,ax=ax[i],s=50,cmap=plt.get_cmap('hot',1024))
        if len(ax) > 1:
            ax[i].set_title(source)
        i += 1

    plt.tight_layout()

    ### Output
    plt.savefig(filename)


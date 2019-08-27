from wpt_test import gatherJSONResults
from tqdm import tqdm
import logging
from pprint import pprint
import sqlite3
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot 
from plotly.subplots import make_subplots

def bootstrap(data, n=1000, func=np.mean):
    """
    Generate `n` bootstrap samples, evaluating `func`
    at each resampling. `bootstrap` returns a function,
    which can be called to obtain confidence intervals
    of interest.
    """
    simulations = list()
    sample_size = len(data)
    xbar_init = np.mean(data)
    for c in range(n):
        itersample = np.random.choice(data, size=sample_size, replace=True)
        simulations.append(func(itersample))
    simulations.sort()
    def ci(p):
        """
        Return 2-sided symmetric confidence interval specified
        by p.
        """
        u_pval = (1+p)/2.
        l_pval = (1-u_pval)
        l_indx = int(np.floor(n*l_pval))
        u_indx = int(np.floor(n*u_pval))
        return(simulations[l_indx],simulations[u_indx])
    return(ci(0.95))

def gatherDicts():
    db = sqlite3.connect('latest/data.sqlite')
    db.row_factory = sqlite3.Row
    sql = db.cursor()
    sql.execute("SELECT * FROM results")
    return sql.fetchall()

def isFirstStep(result):
    if int(result['step']) > 0:
        return False
    else:
        return True

def isUBlock(result):
    if 'ublock' in result['label']:
        return True
    else:
        return False

def isTorBrowser(result):
    if 'tor' in result['location']:
        return True
    else:
        return False

def getPercentile(series,p):
    f = lambda x : np.percentile(x,p)
    r = bootstrap(series,func=f)
    return (f(series),r[0],r[1],len(series))

def getStats(series,name):
    return [ (name+" 1",getPercentile(series,1)),
    (name+" 50",getPercentile(series,50)),
    (name+" 99",getPercentile(series,99))]

def getRequired(series,stddev,margin):
    z = 1.96
    from math import pow
    return pow((z*stddev) / margin,2)

def getEstimates(series,name):
    std = np.std(series)
    #This just returns the estimated number of samples required to calculate the mean within 500ms. 
    return (name,getRequired(series,std,500))

def getBoxSeries(series,name):
    torBrowser = [float(b) for a,b in series if a and b != 'MISSING']
    firefox = [float(b) for a,b in series if not a and b != 'MISSING']
    rS = list()
    rE = list()
    print(name+' has '+str(len(torBrowser)) +' results')
    if len(torBrowser) > 10:
        rS.extend(getStats(torBrowser,name+' Tor Browser'))
        rE.append(getEstimates(torBrowser,name+' Tor Browser'))
    if len(firefox) > 10:
        rS.extend(getStats(firefox,name+' Firefox'))
        rE.append(getEstimates(firefox,name+' Firefox'))
    return (rS,rE)
    
if __name__ == "__main__":
    dicts = gatherDicts()
    metrics = ['firstPaint','SpeedIndex', 'visualComplete85']
    series = dict()
    for m in metrics:
        series[m] = list()

    for m in metrics:
        for d in dicts:
            s = (isFirstStep(d),isUBlock(d),isTorBrowser(d),d[m])
            series[m].append(s)

    rSs = []
    rEs = []
    for k in tqdm(series.keys(),desc='Calculating confidence intervals'):
        vals = series[k]
        firstUBlock = [(c,d) for a,b,c,d in vals if a and b]
        subUblock =[ (c,d) for a,b,c,d in vals if not a and b]
        firstOriginal = [(c,d) for a,b,c,d in vals if a and not b]
        subOriginal = [(c,d) for a,b,c,d in vals if not a and not b]
        rS,rE = getBoxSeries(firstUBlock,k+ ' First, UBlock')
        rSs.extend(rS)
        rEs.extend(rE)
        rS,rE = getBoxSeries(subUblock,k+' Sub,UBlock')
        rSs.extend(rS)
        rEs.extend(rE)
        rS,rE =getBoxSeries(firstOriginal,k+' First,Original')
        rSs.extend(rS)
        rEs.extend(rE)
        rS,rE =getBoxSeries(subOriginal,k+' Sub,Original')
        rSs.extend(rS)
        rEs.extend(rE)
    rSs = sorted(rSs,key=lambda x : x[1][2]-x[1][1],reverse=True)
    rEs = sorted(rEs,key=lambda x : x[1],reverse=True)
    print("Estimated samples to find the mean within 500ms")
    pprint([(n,r) for n,r in rEs])
    print("Series with inaccurate confidence intervals")
    pprint([(n,r[1],r[2],r[3]) for n,r in rSs if r[2]-r[1]>5000])
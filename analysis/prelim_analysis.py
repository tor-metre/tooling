from wpt_test import gatherJSONResults
from tqdm import tqdm
import logging
from pprint import pprint
import sqlite3


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

dicts = gatherDicts()
metrics = ['firstPaint','SpeedIndex', 'visualComplete85']
series = dict()
for m in metrics:
    series[m] = list()

for m in metrics:
    for d in dicts:
        s = (isFirstStep(d),isUBlock(d),isTorBrowser(d),d[m])
        series[m].append(s)

import plotly.graph_objs as go
from plotly.offline import plot 
from plotly.subplots import make_subplots

def getBoxElement(series,name):
    return go.Box(y=series,name=name,boxpoints='all',jitter=0.3,pointpos=-1.8)

def getBoxSeries(series):
    torBrowser = [float(b) for a,b in series if a and b != 'MISSING']
    firefox = [float(b) for a,b in series if not a and b != 'MISSING']
    return [getBoxElement(torBrowser,'Tor Browser'),getBoxElement(firefox,'Firefox')]

for k in tqdm(series.keys(),desc='Drawing graphs'):
    fig = make_subplots(rows=1,cols=4,subplot_titles=['First,UBlock','Sub,UBlock','First,Original','Sub,Original'])
    vals = series[k]
    firstUBlock = [(c,d) for a,b,c,d in vals if a and b]
    subUblock =[ (c,d) for a,b,c,d in vals if not a and b]
    firstOriginal = [(c,d) for a,b,c,d in vals if a and not b]
    subOriginal = [(c,d) for a,b,c,d in vals if not a and not b]
    fig.add_traces(getBoxSeries(firstUBlock),cols=[1,1],rows=[1,1])
    fig.add_traces(getBoxSeries(subUblock),cols=[2,2],rows=[1,1])
    fig.add_traces(getBoxSeries(firstOriginal),cols=[3,3],rows=[1,1])
    fig.add_traces(getBoxSeries(subOriginal),cols=[4,4],rows=[1,1])
    fig.update_yaxes(range=[0,120000])
    fig.update_layout(title_text=k,showlegend=False)
    fig.write_image('graphs/'+str(k)+'.png',width=1920,height=1080)
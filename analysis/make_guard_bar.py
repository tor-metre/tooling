from make_box_plot_compare import listToBox

import sqlite3
from plotly.offline import plot 
import plotly.graph_objects as go
import numpy as np 
from itertools import repeat

query = """
        SELECT VisualComplete85,location   FROM results WHERE step == 0 AND location LIKE '%tor%';
"""
db = sqlite3.connect('latest/data.sqlite')
sql = db.cursor()
sql.execute(query)

series = dict()
for (v,l) in sql.fetchall():
    if l not in series.keys():
        series[l] = list()
    if v == 'MISSING':
        continue
    else:
        series[l].append(float(v))

seriesVals = sorted(series.items(),key=lambda x : np.median(x[1]))
yValues = sorted([np.median(x) for x in series.values()])
seriesColour = ['hsl('+str(h)+',50%'+',50%)' for h in np.linspace(150, 0, len(series.keys()))]

boxes = []
#i = 0
#for location,values in seriesVals:
boxes.append(go.Bar(y=yValues,marker_color=seriesColour))
    #i+= 1
fig = go.Figure()
for b in boxes:
    fig.add_trace(b)

fig.update_layout(showlegend=False)

fig.update_layout(
    title=go.layout.Title(
        text="Median Page Load Time by Tor Client",
        xref="paper",
        x=0,
        font=dict(
            size=80,
        )
    ),
    xaxis=go.layout.XAxis(
        title=go.layout.xaxis.Title(
            text="Tor Client",
        font=dict(
            size=80,
        )
        )
    ),
    yaxis=go.layout.YAxis(
        title=go.layout.yaxis.Title(
            text="Time (Milliseconds)",
        font=dict(
            size=80,
        )
        )
    )
)
fig.update_yaxes(range=[0,50000])
fig.update_xaxes(tickangle=0, tickfont=dict(size=80))
fig.update_yaxes(tickangle=0, tickfont=dict(size=80))

fig.show()
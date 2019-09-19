from make_box_plot_compare import listToBox

import sqlite3
from plotly.offline import plot 
import plotly.graph_objects as go
import numpy as np 
from itertools import repeat

query = """
        SELECT VisualComplete,url   FROM results WHERE step == 0 AND location LIKE '%tor%';
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

seriesVals = sorted(series.items(),key=lambda   x : np.median(x[1]))
seriesColour = ['hsl('+str(h)+',75%'+',40%)' for h in np.linspace(150, 0, len(series.keys()))]

boxes = []
i = 0
for location,values in seriesVals:
    boxes.append(go.Box(y=values,name=location,marker_color=seriesColour[i]))#,boxpoints=False))
    i+= 1
fig = go.Figure()
for b in boxes:
    fig.add_trace(b)
fig.update_yaxes(range=[0,45000])

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
fig.update_yaxes(range=[0,30000])
fig.update_xaxes(tickangle=0, tickfont=dict(size=80))
fig.update_yaxes(tickangle=0, tickfont=dict(size=80))


fig.show()
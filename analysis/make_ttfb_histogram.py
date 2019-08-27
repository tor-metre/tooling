import sqlite3
import plotly.graph_objs as go
from plotly.offline import plot 

from make_box_plot_compare import selectToList

def listToHistogram(data,name):
    return go.Histogram(x=data,name=name,histnorm='probability')
if __name__ == '__main__':
    boxes = [listToHistogram(selectToList("""
        SELECT TTFB FROM results WHERE step == 0 AND location LIKE '%tor%';
    """
    ),"Tor"),
    listToHistogram(selectToList("""
        SELECT TTFB FROM results WHERE step == 0 AND location LIKE '%firefox%';
    """
    ),"Firefox")
    ]

    fig = go.Figure()

    fig.update_layout(barmode='overlay')
  

    for b in boxes:
        fig.add_trace(b)

    fig.update_layout(showlegend=False)

    fig.update_layout(
        title=go.layout.Title(
            text="Distribution of TTFB Across All Requests",
            xref="paper",
            x=0
        ),
        xaxis=go.layout.XAxis(
            title=go.layout.xaxis.Title(
                text="Time to First Byte (miliseconds)",
            )
        ),
        yaxis=go.layout.YAxis(
            title=go.layout.yaxis.Title(
                text="Frequency of Observation (count)",
            )
        )
    )
    
    fig.update_traces(opacity=0.75)
    fig.show()
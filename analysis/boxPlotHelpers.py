import sqlite3
import plotly.graph_objs as go
from plotly.offline import plot 

def selectToList(db,query):
    db = sqlite3.connect(db)
    sql = db.cursor()
    sql.execute(query)
    results = list()
    for r in sql.fetchall():
        results.append(r[0])
    #pprint(results)
    return results 

def listToBox(values,n):
    #TODO set colour based on Firefox/Tor Original/Ublock?
    return go.Box(y=values,name=n,boxpoints=False)#,jitter=0.3,pointpos=-1.8)


def drawBoxes(boxes,title,ylimit=30000,xaxis_title="Location",yaxis_title="Time (Milliseconds)",xaxis_angle=45):
    fig = go.Figure()
    for b in boxes:
        fig.add_trace(b)

    fig.update_layout(showlegend=False)

    fig.update_layout(
        title=go.layout.Title(
            text=title,
            xref="paper",
            x=0,
            font=dict(
                size=24,
            )
        ),
        xaxis=go.layout.XAxis(
            title=go.layout.xaxis.Title(
                text=xaxis_title,
            font=dict(
                size=24,
            )
            )
        ),
        yaxis=go.layout.YAxis(
            title=go.layout.yaxis.Title(
                text=yaxis_title,
            font=dict(
                size=24,
            )
            )
        )
    )
    fig.update_yaxes(range=[0,ylimit])
    fig.update_xaxes(tickangle=xaxis_angle, tickfont=dict(size=18))
    fig.update_yaxes(tickangle=0, tickfont=dict(size=18))
    #fig.show()
    byt = fig.to_image(format="png",width=1366,height=720)
    #print(byt)
    from IPython.display import Image, display
    display(Image(byt))
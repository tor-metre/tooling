# Box Plots of Tor vs Firefox. 85%' Complete 
#Series: 
#Tor
#Firefox
#Adblock Y/N 
#First/Subsequent. 

# 
# So split into 8 series
#

# 8 Select Queries
# 8 Box Plots 
# 

import sqlite3
import plotly.graph_objs as go
from plotly.offline import plot 
from pprint import pprint

def selectToList(query):
    db = sqlite3.connect('short-comparative-run/data.sqlite')
    sql = db.cursor()
    sql.execute(query)
    results = list()
    for r in sql.fetchall():
        results.append(r[0])
    #pprint(results)
    return results 

def listToBox(values,n):
    return go.Box(y=values,name=n,boxpoints=False)#,jitter=0.3,pointpos=-1.8)

if __name__ == '__main__':
    boxes = list()
    # boxes.append(listToBox(selectToList("""
    #      SELECT firstPaint FROM results WHERE step == 0 AND location LIKE '%tor%';
    #  """),'Tor, First Paint'))
    # boxes.append(listToBox(selectToList("""
    #      SELECT firstPaint FROM results WHERE step == 0 AND location LIKE '%firefox%';
    #  """),'Firefox, First Paint'))
    # boxes.append(listToBox(selectToList("""
    #      SELECT visualComplete FROM results WHERE step == 0 AND location LIKE '%tor%';
    #  """),'Tor, Visual Completion'))
    # boxes.append(listToBox(selectToList("""
    #      SELECT visualComplete FROM results WHERE step == 0 AND location LIKE '%firefox%';
    #  """),'Firefox, Visual Completion '))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step == 0 AND location LIKE '%tor-with-timer%' AND label LIKE '%ublock%';
    """),'Tor With Timer Changes and Ublock, First Load'))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step == 0 AND location LIKE '%tor-without-timer%' AND label LIKE '%ublock%';
    """),'Tor Without Timer Changes and Ublock, First Run'))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step == 0 AND location LIKE '%tor-with-timer%' AND label LIKE '%original%';
    """),'Tor With Timer Changes and Original, First Load'))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step == 0 AND location LIKE '%tor-without-timer%' AND label LIKE '%original%';
    """),'Tor Without Timer Changes and Original, First Run'))

    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step != 0 AND location LIKE '%tor-with-timer%' AND label LIKE '%ublock%';
    """),'Tor With Timer Changes and Ublock, Subsequent'))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step != 0 AND location LIKE '%tor-without-timer%' AND label LIKE '%ublock%';
    """),'Tor Without Timer Changes and Ublock, Subsequent'))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step != 0 AND location LIKE '%tor-with-timer%' AND label LIKE '%original%';
    """),'Tor With Timer Changes and Original, Subsequent'))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step != 0 AND location LIKE '%tor-without-timer%' AND label LIKE '%original%';
    """),'Tor Without Timer Changes and Original, Subsequent'))



    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step == 0 AND location LIKE '%firefox%' AND label LIKE '%ublock%';
    """),'Firefox and Ublock, First Load'))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step != 0 AND location LIKE '%firefox%' AND label LIKE '%ublock%';
    """),'Firefox and Ublock, Subsequent'))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step == 0 AND location LIKE '%firefox%' AND label LIKE '%original%';
    """),'Firefox and Original, First Run'))
    boxes.append(listToBox(selectToList("""
        SELECT SpeedIndex FROM results WHERE step != 0 AND location LIKE '%firefox%' AND label LIKE '%original%';
    """),'Firefox and Original, Subsequent'))

    fig = go.Figure()

    for b in boxes:
        fig.add_trace(b)

    fig.update_layout(showlegend=False)

    fig.update_layout(
        title=go.layout.Title(
            text="First Paint and Visual Completition by Browser",
            xref="paper",
            x=0,
            font=dict(
                size=24,
            )
        ),
        xaxis=go.layout.XAxis(
            title=go.layout.xaxis.Title(
                text="Configuration",
            font=dict(
                size=24,
            )
            )
        ),
        yaxis=go.layout.YAxis(
            title=go.layout.yaxis.Title(
                text="Time (Milliseconds)",
            font=dict(
                size=24,
            )
            )
        )
    )
    fig.update_yaxes(range=[0,30000])
    fig.update_xaxes(tickangle=45, tickfont=dict(size=18))
    fig.update_yaxes(tickangle=0, tickfont=dict(size=18))
    fig.show()
# Loop
# Get active locations
# Check queue size + pending size
# If nothing coming, kill location. 

# 1) List of all locations with submitted or awaiting jobs. 
# 2) List of all active instances 

import sqlite3
from utils import rowToLocation
from wpt import WPT
from gcp import GCP

def getUpcomingJobLocations(wpt,sql):
    cmd = """ SELECT region,browser,id FROM jobs WHERE status = 'AWAITING'   
   GROUP BY region,browser,id
   ;"""
    sql.execute(cmd)
    locations = set()
    for r in sql.fetchall():
        locations.add(rowToLocation(r))
    print("There are " + str(len(locations)) + " locations with awaiting jobs")
    activeQueues = set(wpt.getActiveQueues())
    print("There are " + str(len(activeQueues)) + " locations with active queues")
    upcomingActive = locations.union(activeQueues)
    print("There are " + str(len(upcomingActive)) + " unique needed locations")
    return upcomingActive

db = sqlite3.connect('test.db') #TODO FIX
db.row_factory = sqlite3.Row
sql = db.cursor()

if __name__ == '__main__':
    gcp = GCP("tor-metre-personal", "firefox-works", "n1-standard-2", "None")
    server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
    key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
    wpt = WPT(server,key)
    locations = getUpcomingJobLocations(wpt,sql)
    print("There are "+str(len(locations))+" active locations")
    instances = gcp.getActiveInstances()
    for i in instances:
        if 'watchdog' in i['name'] or 'wpt-server' in i['name']:
            continue
        if i['name'] not in locations:
            print("Stopping: "+i['name'])
            gcp.stopInstance(i['name'])

#TODO Also delete instances???

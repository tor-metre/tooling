# Loop
# Get active locations
# Check queue size + pending size
# If nothing coming, kill location. 

# 1) List of all locations with submitted or awaiting jobs. 
# 2) List of all active instances 

import sqlite3
from utils import rowToLocation
from wpt import getActiveQueues
from gcp import getActiveInstances,stopInstance

def getUpcomingJobLocations(sql):
    cmd = """ SELECT region,browser,id FROM jobs WHERE status = 'AWAITING'   
   GROUP BY region,browser,id
   ;"""
    sql.execute(cmd)
    locations = set()
    for r in sql.fetchall():
        locations.add(rowToLocation(r))
    print("There are " + str(len(locations)) + " locations with awaiting jobs")
    activeQueues = set(getActiveQueues())
    print("There are " + str(len(activeQueues)) + " locations with active queues")
    upcomingActive = locations.union(activeQueues)
    print("There are " + str(len(upcomingActive)) + " unique needed locations")
    return upcomingActive

db = sqlite3.connect('test.db') #TODO FIX
db.row_factory = sqlite3.Row
sql = db.cursor()

if __name__ == '__main__':
    locations = getUpcomingJobLocations(sql)
    print("There are "+str(len(locations))+" active locations")
    instances = getActiveInstances()
    for i in instances:
        if 'watchdog' in i['name'] or 'wpt-server' in i['name']:
            continue
        if i['name'] not in locations:
            print("Stopping: "+i['name'])
            stopInstance(i['name'])

#TODO Also delete instances???

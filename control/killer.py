# Loop
# Get active locations
# Check queue size + pending size
# If nothing coming, kill location. 

# 1) List of all locations with submitted or awaiting jobs. 
# 2) List of all active instances 

from wpt import WPT
from gcp import GCP
from jobs import Jobs

def getUpcomingJobLocations(wpt,jobs):
    locations = jobs.getAwaitingLocations()
    print("There are " + str(len(locations)) + " locations with awaiting jobs")
    activeQueues = set(wpt.get_active_job_queues())
    print("There are " + str(len(activeQueues)) + " locations with active queues")
    upcomingActive = locations.union(activeQueues)
    print("There are " + str(len(upcomingActive)) + " unique needed locations")
    return upcomingActive


if __name__ == '__main__':
    gcp = GCP("tor-metre-personal", "firefox-works", "n1-standard-2", "None")
    server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
    key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
    wpt = WPT(server,key)
    jobs = Jobs('test.db')
    locations = getUpcomingJobLocations(wpt,jobs)
    print("There are "+str(len(locations))+" active locations")
    instances = gcp.get_active_instances()
    for i in instances:
        if 'watchdog' in i['name'] or 'wpt-server' in i['name']:
            continue
        if i['name'] not in locations:
            print("Stopping: "+i['name'])
            gcp.stop_instance(i['name'])

#TODO Also delete instances???

import sqlite3
from gcp import GCP
from jobs import getPendingLocations, setJobQueued, setJobFailed, getJobs, getAllLocations
from wpt import WPT
from utils import zoneFromName, locationToRow
from concurrent.futures import ThreadPoolExecutor
from time import sleep

wptserver = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'


def checkandStartInstances(sql,gcp):
    zones = gcp.getZones()
    AllInstances = gcp.getInstances(zones)
    AllInstances = set([x['name'] for x in AllInstances])
    PendingLocations = getPendingLocations(sql)
    ActiveInstances = gcp.getActiveInstances()
    StoppedInstances = gcp.getStoppedInstances()
    ActiveLocations = set([x['name'] for x in ActiveInstances])
    StoppedLocations = set([x['name'] for x in StoppedInstances])
    print('Stopped locations: ' + str(StoppedLocations))
    ToStart = PendingLocations - ActiveLocations
    print('Identified ' + str(len(ToStart)) + ' instances to start')
    for s in ToStart:
        try:
            if s in StoppedLocations:
                print("Restarting instance " + str(s))
                gcp.restartInstance(zoneFromName(s), s)
            else:
                print("Starting instance " + str(s))
                r = locationToRow(s)
                if s in AllInstances:
                    continue  # Do Nothing!
                gcp.startInstance(r['region'], r['browser'], r['id'])
        except Exception as E:
            print("Error starting instance, continuing. Message: " + str(E))
    return True

def getUpcomingJobs(wpt,sql, maxQueueLength=100):
    # Get a list of jobs which should be queued to fill up the buffers.
    queued = wpt.getQueuedJobs()
    toQueueJobs = list()
    for l, t in queued.items():
        print('Considering queue for ' + str(l))
        toQueue = maxQueueLength - t
        print('Need to queue ' + str(toQueue) + ' jobs')
        if toQueue < 1:
            continue
        else:
            notQueued = getJobs(l, 'AWAITING', toQueue, sql,
                                orderby=" ORDER BY iter ASC, step ASC ")  # TODO ORDERBY!!! TODO
            print('Found ' + str(len(notQueued)) + ' jobs to queue')
            toQueueJobs.extend(notQueued)
    return toQueueJobs

def doJob(j):
    db = sqlite3.connect('test.db')  # TODO FIX
    sql = db.cursor()
    i = j['id']
    server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
    key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
    wpt = WPT(server,key)
    r = wpt.submitTest(j, wptserver, key)
    if int(r['statusCode']) == 200:
        setJobQueued(j, r, db, sql)
        return True
    else:
        setJobFailed(j, r, db, sql)
        return False


def submitJobs(jobs):
    executor = ThreadPoolExecutor(max_workers=55)
    futures = executor.map(doJob, jobs)
    executor.shutdown(wait=True)
    return len([x for x in futures if x == True])


def checkAndSubmitJobs(wpt):
    # Get Locations from Server (all configured for)
    db = sqlite3.connect('test.db')  # TODO FIX
    db.row_factory = sqlite3.Row
    sql = db.cursor()
    upcoming = getUpcomingJobs(wpt,sql, maxQueueLength=5)
    # Get Queued Job Totals
    s = submitJobs(upcoming)
    print('Succesfully queued ' + str(s) + ' jobs')
    return True


if __name__ == '__main__':
    # TODO Sort out locations on server! (SSH? Sync? Something else?)
    gcp = GCP("tor-metre-personal", "firefox-works", "n1-standard-2", "None")
    server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
    key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
    locations_file = '/var/www/webpagetest/www/settings/locations.ini'
    wpt = WPT(server,key,locations_file=locations_file)
    iterations = 0
    db = sqlite3.connect('test.db')  # TODO FIX
    db.row_factory = sqlite3.Row
    sql = db.cursor()
    wpt.setServerLocations(getAllLocations(sql))
    checkandStartInstances(sql)
    while True:
        checkAndSubmitJobs(wpt)
        iterations += 1
        if iterations == 4:
            iterations = 0
            checkandStartInstances(sql)
            sleep(10)

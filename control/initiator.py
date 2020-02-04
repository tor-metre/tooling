import sqlite3
from gcp import GCP
from jobs import Jobs
from wpt import WPT
from utils import zone_from_name, location_to_dict
from concurrent.futures import ThreadPoolExecutor
from time import sleep

wptserver = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'

def getUpcomingJobs(wpt,jobs, maxQueueLength=100):
    # Get a list of jobs which should be queued to fill up the buffers.
    queued = wpt.get_job_queues()
    toQueueJobs = list()
    for l, t in queued.items():
        print('Considering queue for ' + str(l))
        toQueue = maxQueueLength - t
        print('Need to queue ' + str(toQueue) + ' jobs')
        if toQueue < 1:
            continue
        else:
            notQueued = jobs.get_jobs_where(l, 'AWAITING', toQueue, orderby=" ORDER BY iter ASC, step ASC ")
            print('Found ' + str(len(notQueued)) + ' jobs to queue')
            toQueueJobs.extend(notQueued)
    return toQueueJobs

def doJob(j):
    i = j['id']
    server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
    key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
    wpt = WPT(server,key)
    jobs = Jobs('test.db')
    r = wpt.submit_test(j)
    if int(r['statusCode']) == 200:
        jobs.set_job_as_queued(j, r)
        return True
    else:
        jobs.set_job_failed(j, r)
        return False


def submitJobs(jobs):
    executor = ThreadPoolExecutor(max_workers=55)
    futures = executor.map(doJob, jobs)
    executor.shutdown(wait=True)
    return len([x for x in futures if x == True])


def checkAndSubmitJobs(wpt,jobs):
    # Get Locations from Server (all configured for)
    upcoming = getUpcomingJobs(wpt,jobs, maxQueueLength=5)
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
    jobs = Jobs('test.db')
    wpt.set_server_locations(jobs.get_unique_job_locations())
    while True:
        checkAndSubmitJobs(wpt,jobs)


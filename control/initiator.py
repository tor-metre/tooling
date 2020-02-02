from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import sqlite3 
from tempfile import SpooledTemporaryFile
from json import loads, dumps
from subprocess import run

wptserver = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'

from wpt_test import submitTest

def doJob(j):
    db = sqlite3.connect('test.db') #TODO FIX
    sql = db.cursor()
    i = j['id']
    r = submitTest(j,wptserver,key)
    if int(r['statusCode']) == 200:
        setJobQueued(j,r,db,sql)
        return True
    else:
        setJobFailed(j,r,db,sql)
        return False

from concurrent.futures import ThreadPoolExecutor

def submitJobs(jobs):
    executor = ThreadPoolExecutor(max_workers=55)
    futures = executor.map(doJob,jobs)
    executor.shutdown(wait=True)
    return len([x for x in futures if x ==True])

def oldsubmitJobs(jobs,server):
    #Submit a list of jobs and return their IDs
    #Essentially already exists, just needs extracting from the database,
    success = 0
    for j in jobs: 
        i = j['id']
        from wpt_test import submitTest
        r = submitTest(j,server,key)
        if int(r['statusCode']) == 200:
            setJobQueued(j,r)
            success += 1
        else:
            setJobFailed(j,r)
            continue
    return success


from subprocess import run 

if __name__ == '__main__':
    #TODO Sort out locations on server! (SSH? Sync? Something else?)
    from time import sleep 
    iterations = 0
    db = sqlite3.connect('test.db') #TODO FIX
    db.row_factory = sqlite3.Row
    sql = db.cursor() 
    setServerLocations(getAllLocations(sql))
    checkandStartInstances(sql) 
    while True:
        checkAndSubmitJobs()
        iterations +=1
        if iterations == 4:
            iterations = 0
            checkandStartInstances(sql)
            sleep(10) 
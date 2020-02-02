from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import sqlite3 
from tempfile import SpooledTemporaryFile
from json import loads, dumps
from subprocess import run

wptserver = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'

def getJobs(location,status,limit,sql,orderby="",):
    #Get all jobs matching a particualr location,status up to some limit
    #Not tested.

    row = locationToRow(location)
    cmd = """ SELECT * FROM jobs where region = '""" + row['region'] + """'
    AND browser = '""" + row['browser'] + """'
    AND id = '""" + row['id'] + """'
    AND status = '"""+str(status)+ "' " + orderby +""" LIMIT """+str(limit)  +";"
    #print(cmd)
    sql.execute(cmd)
    return list(sql.fetchall())


def getUpcomingJobs(sql,maxQueueLength=100):
    #Get a list of jobs which should be queued to fill up the buffers.
    queued = getQueuedJobs()
    toQueueJobs = list()
    for l,t in queued.items():
        print('Considering queue for '+str(l))
        toQueue = maxQueueLength - t
        print('Need to queue '+str(toQueue)+' jobs')
        if toQueue < 1:
            continue 
        else:
            notQueued = getJobs(l,'AWAITING',toQueue,sql,orderby=" ORDER BY iter ASC, step ASC ") #TODO ORDERBY!!! TODO
            print('Found '+str(len(notQueued))+ ' jobs to queue')
            toQueueJobs.extend(notQueued)
    return toQueueJobs

def setJobFailed(j,r,db,sql):
    #Upsert submitted_time, output_location (JSON), queue_ID,status
    newStatus = 'FAILED'
    from datetime import datetime
    submitted_time = datetime.now()
    query = """
        UPDATE jobs
        SET submitted_time = '"""+str(submitted_time)+"""',
            status = '"""+str(newStatus)+"""',
            output_location = '"""+str(r).replace("'","''")+"""'
        WHERE
            region = '"""+str(j['region'])+"""'
            AND browser = '"""+str(j['browser'])+"""'
            AND id = '"""+str(j['id'])+"""'
            AND script = '"""+str(j['script'])+"""'
            AND step = '"""+str(j['step'])+"""'
            AND iter = '"""+str(j['iter'])+"""'
    ;"""
    #print(query)
    sql.execute(query)
    db.commit()
    if sql.rowcount != 1:
        raise RunTimeException("Error performing upsert on " + str(j))

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

def setJobQueued(j,r,db,sql):
    #Upsert submitted_time, output_location (JSON), queue_ID,status
    newStatus = 'SUBMITTED'
    from datetime import datetime
    submitted_time = datetime.now()
    queue_id = r['data']['testId']
    query = """
        UPDATE jobs
        SET submitted_time = '"""+str(submitted_time)+"""',
            queue_id = '"""+str(queue_id)+"""',
            status = '"""+str(newStatus)+"""'
        WHERE
            region = '"""+str(j['region'])+"""'
            AND browser = '"""+str(j['browser'])+"""'
            AND id = '"""+str(j['id'])+"""'
            AND script = '"""+str(j['script'])+"""'
            AND step = '"""+str(j['step'])+"""'
            AND iter = '"""+str(j['iter'])+"""'
    ;"""
    #print(query)
    sql.execute(query)
    db.commit()
    if sql.rowcount != 1:
        raise RunTimeException("Error performing upsert on " + str(j))

def checkAndSubmitJobs():
    #Get Locations from Server (all configured for)
    db = sqlite3.connect('test.db') #TODO FIX
    db.row_factory = sqlite3.Row
    sql = db.cursor()    
    upcoming = getUpcomingJobs(sql,maxQueueLength=5)
    #Get Queued Job Totals
    s = submitJobs(upcoming)
    print('Succesfully queued '+str(s)+' jobs')
    return True

def getPendingLocations(sql):
    #Do Query, get locations with pending jobs
    #Remove any which are active in the server queue 
    query = """
        SELECT region,browser,id FROM jobs WHERE status='AWAITING' GROUP BY region,browser,id
    """
    #print(query)
    sql.execute(query)
    results = sql.fetchall()
    locations = set()
    for r in results:
        locations.add(rowToLocation(r))
    print('Found '+str(len(locations)) + ' pending locations')
    return locations 

def checkandStartInstances(sql):
    #Get locations From server
    #Where offline
    #and exist Queued or Upcoming
    #Start. 
    zones = ['us-central1-a']
    AllInstances = getInstances(zones)
    AllInstances = set([x['name'] for x in AllInstances])
    PendingLocations = getPendingLocations(sql)
    ActiveInstances = getActiveInstances()
    StoppedInstances = getStoppedInstances()
    ActiveLocations = set([x['name'] for x in ActiveInstances])
    StoppedLocations = set([x['name'] for x in StoppedInstances])
    print('Stopped locations: '+str(StoppedLocations))
    ToStart = PendingLocations - ActiveLocations
    print('Identified '+str(len(ToStart))+' instances to start')
    for s in ToStart:
        try:
            if s in StoppedLocations:
                print("Restarting instance "+str(s))
                restartInstance(zoneFromName(s),s)
            else:
                print("Starting instance "+str(s))
                r = locationToRow(s)
                if s in AllInstances:
                    continue #Do Nothing!
                startInstance(r['region'],r['browser'],r['id'])
        except Exception as E:
            print("Error starting instance, continuing. Message: " + str(E))
    return True

from subprocess import run 

def getAllLocations(sql):
    query = """
        SELECT region,browser,id FROM jobs GROUP BY region,browser,id
    """
    sql.execute(query)
    locations = set()
    for r in sql.fetchall():
        l = rowToLocation(r)
        locations.add(l)
    return locations 

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
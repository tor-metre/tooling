from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import sqlite3 


def getInstances(zones):
    results = list()
    for zone in zones:
        credentials = GoogleCredentials.get_application_default()
        service = discovery.build('compute', 'v1', credentials=credentials)
        project = 'moz-fx-dev-djackson-torperf'

        # The name of the zone for this request.
        #zone = 'us-central1-a'  
        request = service.instances().list(project=project, zone=zone)
        while request is not None:
            response = request.execute()
            for instance in response['items']:
                idict = dict()
                idict['name'] = instance['name']
                idict['zone'] = zone 
                idict['creation_time'] = instance['creationTimestamp']
                idict['status'] = instance['status']
                if 'location' in instance['metadata'].keys():
                    idict['location'] = instance['metadata']['location']
                    idict['stateFile'] = instance['metadata']['stateFile']
                results.append(idict)
            request = service.instances().list_next(previous_request=request, previous_response=response)
    return results


def getActiveInstances():
    #Return a list of active GCE instances (that have been up for 60 seconds at least)
    zones = ['us-central1-a']
    results = getInstances(zones)
    up = [r for r in results if r['status'] == 'RUNNING'] #TODO and r['creation_time']]
    return up 

def getStoppedInstances():
    #Return a list of active GCE instances (that have been up for 60 seconds at least)
    zones = ['us-central1-a']
    results = getInstances(zones)
    up = [r for r in results if r['status'] == 'TERMINATED'] #TODO and r['creation_time']]
    return up 

from tempfile import SpooledTemporaryFile
from json import loads, dumps
from subprocess import run

wptserver = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'

def getTesters(wptserver):
    #See which locations the server thinks are up. 
    #Check all active instances appear on this list
    #Its okay if the server thinks some locations are up but the instances are down. It just hasn't realised yet.
    args = ['webpagetest',
            'testers',
            '--server',
            wptserver
    ]
    outT = SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    #Stops us hitting the buffer limit if use pipe.
    #cmd = ""
    #for arg in args:
    #    cmd = cmd + arg + ' '
    #print(cmd)
    result = run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = loads(result) #String to JSON
    #Format (not checked)
    #['data']['location] {id,status,testers}
    return output  


def getQueueStatus(server):
    #See which locations the server thinks are up. 
    #Check all active instances appear on this list
    #Its okay if the server thinks some locations are up but the instances are down. It just hasn't realised yet.
    args = ['webpagetest',
            'locations',
            '--server',
            server
    ]
    outT = SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    #Stops us hitting the buffer limit if use pipe.
    #cmd = ""
    #for arg in args:
    #    cmd = cmd + arg + ' '
    #print(cmd)
    result = run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = loads(result) #String to JSON
    #Format (not checked)
    #['data']['location] {id,status,PendingTests} PendingTests{Total,Testing,Idle}
    return output  

def rowToLocation(row):
    return row['region']+'--'+row['browser']+'--'+row['id']

def locationToRow(location):
    components = location.split('--')
    row = dict()
    row['region'] = components[0]
    row['browser'] = components[1]
    row['id'] = components[2]
    return row

def startInstance(zone,browser,i):
    #Start an instance
    #Handle the case where the instance already exists!
    from start_test import create_instance
    name = rowToLocation({
        'region' : zone,
        'browser' : browser,
        'id' : i
    })
    stateFile = "gs://hungry-serpent//"+str(i)+'.state'
    return create_instance(zone,name,name,stateFile)

def restartInstance(zone,name):
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('compute', 'v1', credentials=credentials)
    project = 'moz-fx-dev-djackson-torperf'
    request = service.instances().start(project=project, zone=zone, instance=name)
    response = request.execute()

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

def getQueuedJobs():
    q = getQueueStatus(wptserver)
    if 'data' not in q['response'].keys():
        #No queues up!
        return dict()
    result = dict()
    if isinstance(q['response']['data']['location'],list):
        for v in q['response']['data']['location']:
            l = v['id']
            t = v['PendingTests']['Total']
            result[l] = t
    else:
        return {
            q['response']['data']['location']['id'] : 
            q['response']['data']['location']['PendingTests']['Total']
        }
    return result

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

def zoneFromName(name):
    components = name.split('--')
    return components[0]

def idFromName(name):
    components = name.split('--')
    return components[2]

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

def setServerLocations(locations):
    #Get all the locations we need. 
    #Push them to the server.ini 
    #Using scp?
    f = open('newLocations.ini','w')
    data = """[locations]
1=Test_loc
default=Test_loc
  
[Test_loc]
1=TESTLOCATIONCHANGEME
"""
    count = 1
    for l in locations:
        count += 1 
        data+=  str(count)+"="+l+"\n"
    data += 'label="Test Location"\n'
    data += """
[TESTLOCATIONCHANGEME]
browser=Chrome,Firefox,Tor Browser
label="Test Location"

"""
    #TODO Add additional lines
    for l in locations:
        data+= "["+l+"]"+"\n"
        if 'tor' in l: 
            data+= "browser=Tor Browser\n"
        else:
            data+= "browser=Firefox\n"
        data+='label="Test Location"\n'
        data += '\n'
    f.write(data)
    f.close()
    args = [
        'cp',
        'newLocations.ini',
        '/var/www/webpagetest/www/settings/locations.ini'
    ]
    run(args)

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
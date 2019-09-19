#Loop:
# Get Finished Jobs
# Download and store them 
# Update DB

import sqlite3 
from time import sleep
from tempfile import SpooledTemporaryFile
from json import loads, dumps
from subprocess import run
from datetime import datetime,timedelta
from tqdm import tqdm 

wptserver = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'

def checkFinished(id,server):

    args = ['webpagetest',
            'status',
            id,
            '--server',
            server
    ]
    outT = SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    result = run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = loads(result) #String to JSON
    if int(output['statusCode']) == 200:
        return True
    else:
        return False

def getJSON(id,server):
    args = ['webpagetest',
            'results',
            id,
            '--server',
            server
    ]
    outT = SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    result = run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = loads(result) #String to JSON
    return output 

from concurrent.futures import ThreadPoolExecutor

def doJob(r):
    try:
        i,t = r
        #checkpoint = datetime.now() - timedelta(0,160) #Probably should autoscale based on expected run time and expected queue size. 
        #if t > str(checkpoint): #TODO 
            #Can we also make use of the order and location here. Don't have to brute force everything! As the order should be stable? Risky?
            #Must be at least X time in queue. 
        #    return None
        #if checkFinished(i,wptserver):
        return i,downloadJob(i)
        #else:
        #    return None 
    except Exception as E:
        print("Error performing job: "+str(E))
        return None 

def getFinished(sql,db):
    #Get Pending where have been pending for >60 seconds
    #Check status with server
    #Return list
    query = """
        SELECT queue_id, submitted_time FROM jobs WHERE status='SUBMITTED' LIMIT 2000;
    """
    sql.execute(query)
    results = list(sql.fetchall())
    print('Checking ' + str(len(results)) + ' new jobs')
    executor = ThreadPoolExecutor(max_workers=40)
    futures = executor.map(doJob,results)
    errors_or_missing = 0
    set_errors = 0
    success = 0
    for fu in tqdm(futures):
        if fu is None:
            errors_or_missing += 1 
            continue
        else:
            i,f = fu
            if f[0]:
                success += 1 
                setFinished(i,sql,db)
            else:
                set_errors += 1 
                setErrors(i,f[1],f[2],sql,db)
    db.commit()
    print("Timestamp: "+str(datetime.now()))
    print("Errors or missing: "+str(errors_or_missing))
    print("Set Errors: "+str(set_errors))
    print("Successes: "+str(success))
    executor.shutdown(wait=True)

def downloadJob(i):
    jRes= getJSON(i,wptserver)
    from wpt_test import saveResults
    return saveResults(jRes,'../temp-steady-street')
    
def setErrors(i,f,e,sql,db):
    query = """
    UPDATE jobs
        SET status = 'ERROR',
            output_location = '"""+str(f)+' '+str(e).replace("'","''")+"""',
            finished_time = '"""+str(datetime.now())+"""'
        WHERE queue_id = '"""+str(i)+"""';
    """
    sql.execute(query)
    return True

def setFinished(i,sql,db):
    query = """
    UPDATE jobs
        SET status = 'FINISHED',
            finished_time = '"""+str(datetime.now())+"""'
        WHERE queue_id = '"""+str(i)+"""';
    """
    sql.execute(query)
    return True

if __name__ == '__main__':
    while True:
        db = sqlite3.connect('test.db') 
        db.row_factory = sqlite3.Row
        sql = db.cursor()
        getFinished(sql,db)
        sleep(1)

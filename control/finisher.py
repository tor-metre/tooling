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

if __name__ == '__main__':
    while True:
        db = sqlite3.connect('test.db') 
        db.row_factory = sqlite3.Row
        sql = db.cursor()
        getFinished(sql,db)
        sleep(1)

# 
# Tool for creating new jobs
# and the database

import sqlite3
from utils import gatherScripts
from jobs import Jobs

dbLocation = "test.db" #TODO Fix
db = sqlite3.connect(dbLocation)
sql = db.cursor()

def generateJobs(jobs,regions,browsers,ids,scripts,reps):
    #Dispatch job creation
    total = 0
    for r in regions:
        for b in browsers:
            for i in ids:
                for rp in reps:
                    step = 0
                    for s in scripts.values():
                        jobs.createJob(r,b,i,s,step,rp)
                        step += 1 
                        total += 1
    db.commit()
    print(str(total)+' jobs created')

if __name__ == '__main__':
    #Do things
    jobs = Jobs('test.db')
    scripts = gatherScripts('../wpt-instrumentation/baseline/original')
    generateJobs(jobs,['us-central1-a'],['tor-without-timer'],range(1000,1010),scripts,range(2))
    generateJobs(jobs,['us-central1-a'],['tor-with-timer'],range(1010,1020),scripts,range(2))
    scripts = gatherScripts('../wpt-instrumentation/baseline/ublock')
    generateJobs(jobs,['us-central1-a'],['tor-without-timer'],range(1020,1030),scripts,range(2))
    generateJobs(jobs,['us-central1-a'],['tor-with-timer'],range(1030,1040),scripts,range(2))

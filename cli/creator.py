# 
# Tool for creating new jobs
# and the database

import sqlite3
from tooling.utiliy.wpt_test import gatherScripts
from datetime import datetime

dbLocation = "test.db" #TODO Fix
db = sqlite3.connect(dbLocation)
sql = db.cursor()

def createDB():
    #TODO Create Statement
    cmd = """
    CREATE TABLE IF NOT EXISTS `jobs` (
	`region`	TEXT,
	`browser`	TEXT,
	`id`	TEXT,
	`script`	TEXT,
	`status`	TEXT,
	`queue_id`	TEXT UNIQUE,
    `output_location`	TEXT,
    `created_time` TEXT,
	`submitted_time`	TEXT,
	`finished_time`	TEXT,
	`step`	INTEGER,
	`iter`	INTEGER,
	PRIMARY KEY(`region`,`browser`,`id`,`script`,`step`,`iter`)
    );"""
    sql.execute(cmd)
    db.commit()
    return True

def escape(s):
    return "'" + str(s) + "'"

def createJob(region,browser,id,script,step,iteration):
    #Create a particular job row.
    status = "AWAITING" 
    t = datetime.now()
    cmd = "INSERT INTO jobs "
    cmd += " ( region,browser,id,script,step,iter,status,created_time )"
    cmd += " VALUES ("
    cmd += escape(region) + ", " + escape(browser) + ", " + escape(id) + ", " \
        + escape(script) + ", " + escape(step) + ", " + escape(iteration) +", "+escape(status) +', '+escape(t)
    cmd += ");"
    #print(cmd)
    sql.execute(cmd)


def generateJobs(regions,browsers,ids,scripts,reps):
    #Dispatch job creation
    total = 0
    for r in regions:
        for b in browsers:
            for i in ids:
                for rp in reps:
                    step = 0
                    for s in scripts.values():
                        createJob(r,b,i,s,step,rp)
                        step += 1 
                        total += 1
    db.commit()
    print(str(total)+' jobs created')

if __name__ == '__main__':
    #Do things
    createDB()
    scripts = gatherScripts('../wpt-instrumentation/baseline/original')
    generateJobs(['us-central1-a'],['tor-without-timer'],range(1000,1010),scripts,range(2))
    generateJobs(['us-central1-a'],['tor-with-timer'],range(1010,1020),scripts,range(2))
    scripts = gatherScripts('../wpt-instrumentation/baseline/ublock')
    generateJobs(['us-central1-a'],['tor-without-timer'],range(1020,1030),scripts,range(2))
    generateJobs(['us-central1-a'],['tor-with-timer'],range(1030,1040),scripts,range(2))

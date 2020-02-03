from utils import dict_to_location, location_to_dict
from datetime import datetime
import sqlite3

def escape(s):
    return "'" + str(s) + "'"

class Jobs:

    def __init__(self, db_path):
        self.db = sqlite3.connect('db_path')
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        self._createDB()

    def _createDB(self):
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
        self.cursor.execute(cmd)
        self.persist()

    def persist(self):
        self.db.commit()

    def createJob(self,region, browser, id, script, step, iteration):
        # Create a particular job row.
        status = "AWAITING"
        t = datetime.now()
        cmd = "INSERT INTO jobs "
        cmd += " ( region,browser,id,script,step,iter,status,created_time )"
        cmd += " VALUES ("
        cmd += escape(region) + ", " + escape(browser) + ", " + escape(id) + ", " \
               + escape(script) + ", " + escape(step) + ", " + escape(iteration) + ", " + escape(
            status) + ', ' + escape(t)
        cmd += ");"
        # print(cmd)
        self.cursor.execute(cmd)

    def getAllLocations(self):
        query = "SELECT region,browser,id FROM jobs GROUP BY region,browser,id"
        self.cursor.execute(query)
        return set([dict_to_location(r) for r in self.cursor.fetchall()])

    def setJobQueued(self, job, result):
        newStatus = 'SUBMITTED'
        submitted_time = datetime.now()
        queue_id = result['data']['testId']
        query = """
            UPDATE jobs
            SET submitted_time = '""" + str(submitted_time) + """',
                queue_id = '""" + str(queue_id) + """',
                status = '""" + str(newStatus) + """'
            WHERE
                region = '""" + str(job['region']) + """'
                AND browser = '""" + str(job['browser']) + """'
                AND id = '""" + str(job['id']) + """'
                AND script = '""" + str(job['script']) + """'
                AND step = '""" + str(job['step']) + """'
                AND iter = '""" + str(job['iter']) + """'
        ;"""
        self.cursor.execute(query)
        self.persist()
        if self.cursor.rowcount != 1:
            raise RuntimeError("Error performing upsert on " + str(job))

    def getPendingLocations(self):
        # Do Query, get locations with pending jobs
        # Remove any which are active in the server queue
        query = """
            SELECT region,browser,id FROM jobs WHERE status='AWAITING' GROUP BY region,browser,id
        """
        # print(query)
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        locations = set([dict_to_location(r) for r in self.cursor.fetchall()])
        print('Found ' + str(len(locations)) + ' pending locations')
        return locations

    def getJobs(self, location, status, limit, orderby="", ):
        row = location_to_dict(location)
        cmd = """ SELECT * FROM jobs where region = '""" + row['region'] + """'
        AND browser = '""" + row['browser'] + """'
        AND id = '""" + row['id'] + """'
        AND status = '""" + str(status) + "' " + orderby + """ LIMIT """ + str(limit) + ";"
        # print(cmd)
        self.cursor.execute(cmd)
        return list(self.cursor.fetchall())

    def getAwaitingLocations(self):
        cmd = """ SELECT region,browser,id FROM jobs WHERE status = 'AWAITING'   
           GROUP BY region,browser,id
           ;"""
        self.cursor.execute(cmd)
        return set([dict_to_location(r) for r in self.cursor.fetchall()])

    def getSubmitted(self):
        query = """
            SELECT queue_id, submitted_time FROM jobs WHERE status='SUBMITTED' LIMIT 2000;
        """
        self.cursor.execute(query)
        return list(self.cursor.fetchall())

    def setJobFailed(self, job, result):
        # Upsert submitted_time, output_location (JSON), queue_ID,status
        newStatus = 'FAILED'
        submitted_time = datetime.now()
        query = """
            UPDATE jobs
            SET submitted_time = '""" + str(submitted_time) + """',
                status = '""" + str(newStatus) + """',
                output_location = '""" + str(result).replace("'", "''") + """'
            WHERE
                region = '""" + str(job['region']) + """'
                AND browser = '""" + str(job['browser']) + """'
                AND id = '""" + str(job['id']) + """'
                AND script = '""" + str(job['script']) + """'
                AND step = '""" + str(job['step']) + """'
                AND iter = '""" + str(job['iter']) + """' ;"""
        self.cursor.execute(query)
        self.persist()
        if self.cursor.rowcount != 1:
            raise RuntimeError("Error performing upsert on " + str(job))

    def setErrors(self, job_id, f, e):
        query = """
        UPDATE jobs
            SET status = 'ERROR',
                output_location = '""" + str(f) + ' ' + str(e).replace("'", "''") + """',
                finished_time = '""" + str(datetime.now()) + """'
            WHERE queue_id = '""" + str(job_id) + """';
        """
        self.cursor.execute(query)
        return True

    def setFinished(self, job_id):
        query = """
        UPDATE jobs
            SET status = 'FINISHED',
                finished_time = '""" + str(datetime.now()) + """'
            WHERE queue_id = '""" + str(job_id) + """';
        """
        self.cursor.execute(query)
        return True

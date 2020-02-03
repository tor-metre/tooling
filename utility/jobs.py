from utils import dict_to_location, location_to_dict
from datetime import datetime
import sqlite3
import logging


class Jobs:

    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        self.create_db()
        self.logger = logging.getLogger("utility." + __name__)
        self.logger.debug(f"Initialised logging for Jobs Object attached to database {db_path}")

    def create_db(self):
        cmd = (""
               "            CREATE TABLE IF NOT EXISTS `jobs` ("
               "        	`job_id`	INTEGER PRIMARY KEY,"
               "        	`experiment_id`	TEXT,"
               "        	`wpt_id`	TEXT UNIQUE,"
               "        	`status`	TEXT,"
               "        	`zone`	TEXT,"
               "        	`browser`	TEXT,"
               "        	`agent_id`	TEXT,"
               "        	`script`	TEXT,"
               "            `output_location`	TEXT,"
               "            `created_time` TEXT,"
               "        	`submitted_time`	TEXT,"
               "        	`finished_time`	TEXT"
               "            );")
        self.cursor.execute(cmd)
        self.persist()

    def persist(self):
        self.db.commit()

    def create_job(self, zone, browser, agent_id, script, experiment_id):
        status = "AWAITING"
        t = datetime.now()
        cmd = f"INSERT INTO jobs (zone,browser,agent_id,experiment_id,script,status,created_time) " \
              f"VALUES ('{zone}','{browser}','{agent_id}','{experiment_id}','{script}','{status}','{t}');"
        self.cursor.execute(cmd)
        assert (self.cursor.lastrowid is not None)
        self.logger.debug(f"Created job with id: {self.cursor.lastrowid}")
        return self.cursor.lastrowid

    def set_job_as_submitted(self, job_id, result):
        submitted_time = datetime.now()
        status = 'SUBMITTED'
        wpt_id = result['data']['testId']
        cmd = f"UPDATE jobs SET submitted_time = '{submitted_time}', wpt_id={wpt_id}, status='{status}'" \
              f"WHERE job_id = {job_id};"
        self.cursor.execute(cmd)
        assert (self.cursor.rowcount == 1)
        self.logger.debug(f"Set as submitted: {job_id}")
        return True

    def set_job_as_error_submitting(self, job_id, result):
        submitted_time = datetime.now()
        status = 'ERROR_SUBMITTING'
        cmd = f"UPDATE jobs SET submitted_time = '{submitted_time}', output_location={result}, status='{status}'" \
              f"WHERE job_id = {job_id};"
        self.cursor.execute(cmd)
        assert (self.cursor.rowcount == 1)
        self.logger.debug(f"Set as error on submitting: {job_id}")
        return True

    def set_job_as_error_testing(self, job_id, result):
        finished_time = datetime.now()
        status = 'ERROR_TESTING'
        cmd = f"UPDATE jobs SET finished_time = '{finished_time}', output_location={result}, status='{status}'" \
              f"WHERE job_id = {job_id};"
        self.cursor.execute(cmd)
        assert (self.cursor.rowcount == 1)
        self.logger.debug(f"Set as error on testing: {job_id}")
        return True

    def set_job_as_finished(self, job_id, output_location):
        finished_time = datetime.now()
        status = 'FINISHED'
        cmd = f"UPDATE jobs SET finished_time = '{finished_time}', output_location={output_location}," \
              f" status='{status}' WHERE job_id = {job_id};"
        self.cursor.execute(cmd)
        assert (self.cursor.rowcount == 1)
        self.logger.debug(f"Set as finished: {job_id}")
        return True

    def get_unique_job_locations(self):
        query = "SELECT zone,browser,agent_id FROM jobs GROUP BY zone,browser,agent_id "
        self.cursor.execute(query)
        results = set([dict_to_location(r) for r in self.cursor.fetchall()])
        self.logger.debug(f'Found {len(results)} job locations')
        return results

    def get_pending_locations(self):
        query = "SELECT zone,browser,agent_id FROM jobs WHERE status='AWAITING' GROUP BY zone,browser,agent_id"
        self.cursor.execute(query)
        locations = set([dict_to_location(r) for r in self.cursor.fetchall()])
        self.logger.debug(f'Found {len(locations)} job locations with pending jobs')
        return locations

    def get_awaiting_jobs(self, location, limit):
        row = location_to_dict(location)
        cmd = f"SELECT job_id FROM jobs WHERE zone = '{row['zone']}' AND browser = '{row['browser']}' AND " \
              f"agent_id = '{row['agent_id']}' AND status = '{'AWAITING'}' ORDER BY job_id LIMIT {str(limit)};"
        self.cursor.execute(cmd)
        results = list(self.cursor.fetchall())
        self.logger.debug(f'Found {len(results)} jobs waiting to be submitted to {location}')
        return results

    def get_submitted_jobs(self):
        # TODO Should this be ordered or filtered by submitted time?
        query = """
            SELECT wpt_id, submitted_time FROM jobs WHERE status='SUBMITTED' LIMIT 2000;
        """
        self.cursor.execute(query)
        results = list(self.cursor.fetchall())
        self.logger.debug(f'Found {len(results)} submitted jobs')
        return results

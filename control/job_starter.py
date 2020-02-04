from wpt import WPT
from jobs import Jobs
import logging
import time


def get_jobs_to_queue(wpt, jobs, max_queue_length=100):
    queues = wpt.get_job_queues()
    logging.debug(f"Considering {len(queues.keys())} queues with a maximum length of {max_queue_length}")
    jobs_to_submit = list()
    for queue, length in queues.items():
        num_to_add = max_queue_length - length
        if num_to_add < 0:
            continue
        else:
            logging.debug(f'Looking for {num_to_add} jobs to enqueue for {queue}')
            jobs_to_add = jobs.get_awaiting_jobs(queue, num_to_add)
            logging.debug(f"Discovered {len(jobs_to_add)} jobs to submit for {queue}")
            jobs_to_submit.extend(jobs_to_add)
    logging.debug(f"In total, discovered {len(jobs_to_submit)} to queue for {len(queues.keys())} queues")
    return jobs_to_submit


def submit_jobs(wpt, jobs, queue):
    succeeded = 0
    error_submission = 0
    for job in queue:
        (success, value) = wpt.submit_test(job)
        if success:
            succeeded += 1
            jobs.set_job_as_submitted(job['job_id'], value)
            logging.debug(f"Successfully submitted job {job['job_id']} as WPT job {value}")
        else:
            error_submission += 1
            logging.warning(f"Error submitting {job['job_id']} Error message: {value}")
            jobs.set_job_as_error_submitting(job['job_id'], value)
    logging.info(f"{len(queue)} jobs. {succeeded} succeeded. {error_submission} errors upon submission.")


def main():
    server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
    key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
    locations_file = '/var/www/webpagetest/www/settings/locations.ini'
    wpt = WPT(server, key, locations_file=locations_file)
    jobs = Jobs('test.db')
    while True:
        wpt.set_server_locations(jobs.get_unique_job_locations())
        submit_jobs(wpt, jobs, get_jobs_to_queue(wpt, jobs, max_queue_length=100))
        time.sleep(60)


if __name__ == '__main__':
    main()

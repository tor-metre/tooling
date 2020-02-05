
from jobs import Jobs
from wpt import WPT, successful_result
import logging
import time


def update_job(wpt,jobs,job):
    job_id = job['wpt_id']
    result = wpt.get_test_result(job_id)
    if successful_result(result):
        jobs.set_job_as_finished(job_id)
        return True
    else:
        jobs.set_job_as_error_testing(job_id, "UNIMPLEMENTED")  # TODO Implement
        logging.warning(f"Job {job_id} with queue id {job['wpt_id']} failed during testing with reason UNIMPLEMENTED")
        return False


def main():
    jobs = Jobs('test.db')
    server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
    key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
    wpt = WPT(server, key)
    while True:
        successful = 0
        failed = 0
        candidate_finished = jobs.get_oldest_submitted_jobs()
        for c in candidate_finished:
            if update_job(wpt, jobs, c):
                successful += 1
            else:
                failed += 1
        logging.info(f"Checked {len(candidate_finished)} jobs. {successful} successfully finished, {failed} had errors "
                     f"during testing.")
        time.sleep(60)


if __name__ == "main":
    main()

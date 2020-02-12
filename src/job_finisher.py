import logging
from utility.wpt import WPT, successful_result
from utility.jobs import Jobs
import time
from utility import configuration as cl


def update_job(wpt, jobs, job):
    job_id = job['wpt_id']
    result = wpt.get_test_result(job_id)
    if successful_result(result):
        jobs.set_job_as_finished(job_id)
        return True
    else:
        jobs.set_job_as_error_testing(job_id, "UNIMPLEMENTED")  # TODO Implement
        logging.warning(f"Job {job_id} with queue id {job['wpt_id']} failed during testing with reason UNIMPLEMENTED")
        return False


def main(config):
    jobs = Jobs(config[cl.JOBS_DB_PATH_ENTRY])
    wpt = WPT(config[cl.WPT_SERVER_URL_ENTRY], config[cl.WPT_API_KEY_ENTRY])
    while True:
        successful = 0
        failed = 0
        candidate_finished = jobs.get_oldest_submitted_jobs(config['max_batch_size'])
        for c in candidate_finished:
            if update_job(wpt, jobs, c):
                successful += 1
            else:
                failed += 1
        logging.info(f"Checked {len(candidate_finished)} jobs. {successful} successfully finished, {failed} had errors "
                     f"during testing.")
        jobs.persist()
        time.sleep(config['sleep_duration'])


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    defaults = {cl.FILE_CONFIG_PATH_ENTRY: 'settings.yaml',
                cl.WPT_SERVER_URL_ENTRY: None,
                cl.WPT_API_KEY_ENTRY: None,
                cl.JOBS_DB_PATH_ENTRY: 'jobs.sqlite'}
    parser = cl.get_core_args_parser('Orchestrates the creation of jobs in WPT')
    parser.add_argument("--sleep-duration", type=int, default=60,
                        help='How many seconds to sleep before between checking the queues and inserting jobs')
    parser.add_argument("--max-batch-size", type=int, default=100,
                        help='Maximum number of jobs to check at a time')
    cl.add_wpt_args(parser)
    cl.add_wpt_location_args(parser)
    cl.add_jobs_args(parser)
    config_result, returned_config = cl.get_config(fixed_config=vars(parser.parse_args()), default_config=defaults)
    if config_result:
        main(returned_config)
    else:
        logging.critical("Invalid configuration. Quitting...")

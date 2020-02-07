from wpt import WPT
from jobs import Jobs
import logging
import time
import configuration as cl


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


def main(config):
    wpt = WPT(config[cl.WPT_SERVER_URL_ENTRY], config[cl.WPT_API_KEY_ENTRY], locations_file=cl.WPT_LOCATIONS_PATH_ENTRY)
    jobs = Jobs(config[cl.JOBS_DB_PATH_ENTRY])
    while True:
        wpt.set_server_locations(jobs.get_unique_job_locations())
        submit_jobs(wpt, jobs, get_jobs_to_queue(wpt, jobs, max_queue_length=config['max-queue-length']))
        time.sleep(config['sleep-duration'])


if __name__ == '__main__':
    defaults = {cl.FILE_CONFIG_PATH_ENTRY: 'settings.yaml',
                cl.WPT_SERVER_URL_ENTRY: None,
                cl.WPT_API_KEY_ENTRY: None,
                cl.WPT_LOCATIONS_PATH_ENTRY: '/var/www/webpagetest/www/settings/locations.ini',
                cl.JOBS_DB_PATH_ENTRY: 'jobs.sqlite'}
    parser = cl.get_core_args_parser('Orchestrates the creation of jobs in WPT')
    parser.add_argument("--sleep-duration", type=int, default=60,
                        help='How many seconds to sleep before between checking the queues and inserting jobs')
    parser.add_argument("--max-queue-length", type=int, default=100,
                        help='Maximum length of the WPT job queue for each location')
    cl.add_wpt_args(parser)
    cl.add_wpt_location_args(parser)
    cl.add_jobs_args(parser)
    result, c = cl.get_config(fixed_config=vars(parser.parse_args()), default_config=defaults)
    if result:
        main(c)
    else:
        logging.critical("Invalid configuration. Quitting...")

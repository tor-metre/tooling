import logging
from utility.wpt import WPT
import time
from utility import configuration as cl
import experiment

def get_jobs_to_queue(wpt, max_queue_length=100):
    queues = wpt.get_job_locations()
    logging.debug(f"Considering {len(queues.keys())} queues with a maximum length of {max_queue_length}")
    jobs_to_submit = list()
    for queue, length in queues.items():
        num_to_add = max_queue_length - length
        if num_to_add < 0:
            continue
        else:
            logging.debug(f'Looking for {num_to_add} jobs to enqueue for {queue}')
            jobs_to_add = experiment.get_awaiting_jobs_by_wpt_location(queue, num_to_add)
            logging.debug(f"Discovered {len(jobs_to_add)} jobs to submit for {queue}")
            jobs_to_submit.extend(jobs_to_add)
    logging.debug(f"In total, discovered {len(jobs_to_submit)} to queue for {len(queues.keys())} queues")
    return jobs_to_submit


def submit_jobs(wpt, jobs_to_submit):
    succeeded = 0
    error_submission = 0
    for job in jobs_to_submit:
        (success, value) = wpt.submit_test(job)
        if success:
            succeeded += 1
            job.set_submitted(value)
            logging.debug(f"Successfully submitted job {job.id} as WPT job {value}")
        else:
            error_submission += 1
            logging.warning(f"Error submitting {job.id} Error message: {value}")
            job.set_error_submission(value)
    logging.info(f"{len(jobs_to_submit)} jobs considered. {succeeded} succeeded. {error_submission} errors upon submission.")


def main(config):
    experiment.init_database(config[cl.JOBS_DB_PATH_ENTRY])
    wpt = WPT(config[cl.WPT_SERVER_URL_ENTRY], config[cl.WPT_API_KEY_ENTRY], locations_file=config[cl.WPT_LOCATIONS_PATH_ENTRY])
    while True:
        wpt.set_server_locations(experiment.get_all_wpt_locations())
        submit_jobs(wpt, get_jobs_to_queue(wpt, max_queue_length=config['max_queue_length']))
        time.sleep(config['sleep_duration'])


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
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

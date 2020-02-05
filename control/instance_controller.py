import logging
from wpt import WPT
from gcp import GCP
from jobs import Jobs
import time
import configuration as cl


def get_instances_to_start(gcp, jobs, all_instances=None):
    if all_instances is None:
        all_instances = gcp.get_instances()
    pending_locations = jobs.get_pending_locations()
    running_locations = set(gcp.get_running_instances(instances=all_instances))
    locations_to_start = pending_locations - set([x['name'] for x in running_locations])
    logging.debug(f"Identified {len(locations_to_start)} instances to be started")
    return locations_to_start


def get_instances_to_stop(gcp, wpt, jobs, all_instances=None):
    if all_instances is None:
        all_instances = gcp.get_instances()
    queues_awaiting_submissions = set(jobs.get_pending_locations())
    queues_with_jobs = set(wpt.get_active_job_queues())
    active_queues = queues_awaiting_submissions.union(queues_with_jobs)
    logging.debug(f"There are {len(active_queues)} active queues.")
    all_instances = set([r['name'] for r in gcp.get_running_instances(instances=all_instances)])
    logging.debug(f"There are {len(all_instances)} active instances.")
    to_stop = set([i for i in all_instances if i not in ['wpt-server'] and i not in active_queues])
    logging.debug(f"Identified {len(to_stop)} instances which can be stopped.")
    return to_stop


def get_maybe_stuck_instances(wpt, gcp, all_instances=None):
    if all_instances is None:
        all_instances = gcp.get_instances()
    running_instances = set([x['name'] for x in gcp.get_running_instances(instances=all_instances)])
    active_queues = set(wpt.get_active_job_queues())
    possible_stuck = running_instances - active_queues
    possible_stuck = [x for x in possible_stuck if 'wpt-server' not in x]
    logging.debug(f"Identified {len(possible_stuck)} possibly stuck instances")
    return set(possible_stuck)


def main():
    # TODO Finish the integration here
    server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
    key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
    wpt = WPT(server, key)
    gcp = GCP("tor-metre-personal", "firefox-works", "n1-standard-2", "None")
    jobs = Jobs('test-db.sqlite')
    sleep_duration = 180
    old_stuck = set()
    logging.info(f"Beginning Instance Controller loop for project {gcp.project}, "
                 f"job database {jobs.db_path} and WPT server {wpt.server}")
    while True:
        instances = gcp.get_instances()
        to_start = get_instances_to_start(gcp, jobs, all_instances=instances)
        to_stop = get_instances_to_stop(gcp, wpt, jobs, all_instances=instances)
        maybe_stuck = get_maybe_stuck_instances(wpt, gcp, all_instances=instances)
        if len(maybe_stuck) > 0:
            logging.warning(f"{len(maybe_stuck)} instances may be stuck")
        definitely_stuck = maybe_stuck.intersection(old_stuck)

        assert (len(to_start.intersection(to_stop)) == 0)
        assert (len(to_start.intersection(definitely_stuck)) == 0)
        assert (len(to_stop.intersection(definitely_stuck)) == 0)

        logging.info(f"{len(to_start)} to be started. {len(to_stop)} to be stopped")
        if len(definitely_stuck) > 0:
            logging.critical(f"{len(definitely_stuck)} are stuck")

        gcp.activate_instances(to_start, instances=instances)
        gcp.deactivate_instances(to_stop, instances=instances)

        for stuck in definitely_stuck:
            logging.critical(f"Instance {stuck} appears to be stuck.")

        old_stuck = maybe_stuck
        logging.debug(f"Sleeping for {sleep_duration} seconds")
        time.sleep(sleep_duration)


if __name__ == "main":
    defaults = {cl.FILE_CONFIG_PATH_ENTRY: 'settings.yaml',
                cl.WPT_SERVER_URL_ENTRY: None,
                cl.WPT_API_KEY_ENTRY: None,
                cl.JOBS_DB_PATH_ENTRY: 'jobs.sqlite'} #TODO - Add the GCP Instance Keys
    parser = cl.get_core_args_parser('Handles instance creation, monitoring and shutdown on GCP')
    parser.add_argument("--sleep-duration", type=int, default=180,
                        help='How many seconds to sleep before between checking the queues and inserting jobs')
    cl.get_full_args_parser("Handles instance creation, monitoring and shutdown on GCP",wpt_location=False)
    result, c = cl.get_config(fixed_config=parser.parse_args(), default_config=defaults)
    if result:
        main(c)
    else:
        logging.critical("Invalid configuration. Quitting...")


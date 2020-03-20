import logging
from utility.wpt import WPT
from utility.gcp import GCP
import experiment
import time
from utility import configuration as cl

logger = logging.getLogger("instance_controller")


def get_instances_to_start(gcp, all_instances=None):
    if all_instances is None:
        all_instances = gcp.get_instances()
    running_instances = set([x['name'] for x in gcp.get_running_instances(instances=all_instances)])
    instances_with_work = set([x.gcp_name for x in experiment.get_pending_instances()])
    instances_to_start = instances_with_work - running_instances
    logger.debug(f"Identified {len(instances_to_start)} instances to be started")
    return instances_to_start


def get_instances_to_stop(gcp, wpt, all_instances=None):
    if all_instances is None:
        all_instances = gcp.get_instances()
    locations_with_work = set([x.wpt_location for x in experiment.get_pending_instances()])
    locations_with_jobs = set(wpt.get_busy_locations())
    intended_active_locations = locations_with_work.union(locations_with_jobs)
    intended_active_instances = set([experiment.wpt_location_to_gcp_name(x) for x in intended_active_locations])
    logger.debug(f"There are {len(intended_active_instances)}  intended active instances.")
    all_instances = set([r['name'] for r in gcp.get_running_instances(instances=all_instances)])
    logger.debug(f"There are {len(all_instances)} actual active instances.")
    to_stop = set([i for i in all_instances if i not in ['wpt-server'] and i not in intended_active_instances])
    logger.debug(f"Identified {len(to_stop)} instances which can be stopped.")
    return to_stop

def get_instances_to_delete(gcp,all_instances=None):
    #TODO Delete instances that won't have any more jobs for at least an hour
    return list()

def get_maybe_stuck_instances(wpt, gcp, all_instances=None):
    #TODO Probably a better way to do this now we have more state in sqlite
    if all_instances is None:
        all_instances = gcp.get_instances()
    running_instances = set([x['name'] for x in gcp.get_running_instances(instances=all_instances)])
    intended_active_locations = wpt.get_busy_locations()
    intended_active_instances = set([experiment.wpt_location_to_gcp_name(x) for x in intended_active_locations])
    possible_stuck = running_instances - intended_active_instances
    possible_stuck = [x for x in possible_stuck if 'wpt-server' not in x]
    logger.debug(f"Identified {len(possible_stuck)} possibly stuck instances")
    return set(possible_stuck)


def main(config):
    wpt = WPT(config[cl.WPT_SERVER_URL_ENTRY], config[cl.WPT_API_KEY_ENTRY],locations_file=config[cl.WPT_LOCATIONS_PATH_ENTRY])
    gcp = GCP(config[cl.GCP_PROJECT_NAME_ENTRY], config[cl.WPT_SERVER_URL_ENTRY],config[cl.WPT_LOCATION_KEY_ENTRY])
    experiment.init_database(config[cl.JOBS_DB_PATH_ENTRY])
    sleep_duration = config['sleep_duration']
    old_stuck = set()
    logger.info(f"Beginning Instance Controller loop for project {gcp.project}, "
                 f"job database {config[cl.JOBS_DB_PATH_ENTRY]} and WPT server {wpt.server}")
    while True:
        instances = gcp.get_instances()
        wpt.set_server_locations(experiment.get_all_instances())
        to_start = get_instances_to_start(gcp, all_instances=instances)
        to_stop = get_instances_to_stop(gcp, wpt, all_instances=instances)
        maybe_stuck = get_maybe_stuck_instances(wpt, gcp, all_instances=instances)
        if len(maybe_stuck) > 0:
            logger.warning(f"{len(maybe_stuck)} instances may be stuck")
        definitely_stuck = maybe_stuck.intersection(old_stuck)

        assert (len(to_start.intersection(to_stop)) == 0)
        assert (len(to_start.intersection(definitely_stuck)) == 0)
        assert (len(to_stop.intersection(definitely_stuck)) == 0)

        logger.info(f"{len(to_start)} to be started. {len(to_stop)} to be stopped")
        if len(definitely_stuck) > 0:
            logger.critical(f"{len(definitely_stuck)} are stuck")

        to_start = [experiment.get_instance_by_gcp_name(x) for x in to_start]
        to_stop = [experiment.get_instance_by_gcp_name(x) for x in to_stop]
        gcp.activate_instances(to_start, instances=instances)
        gcp.deactivate_instances(to_stop, instances=instances)
        for stuck in definitely_stuck:
            logger.critical(f"Instance {stuck} appears to be stuck.")

        old_stuck = maybe_stuck
        logger.debug(f"Sleeping for {sleep_duration} seconds")
        time.sleep(sleep_duration)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    defaults = {cl.FILE_CONFIG_PATH_ENTRY: 'settings.yaml',
                cl.WPT_SERVER_URL_ENTRY: None,
                cl.WPT_API_KEY_ENTRY: None,
                cl.JOBS_DB_PATH_ENTRY: 'experiment.db',
                cl.GCP_PROJECT_NAME_ENTRY: None,
                cl.GCP_IMAGE_NAME_ENTRY: None,
                cl.GCP_INSTANCE_TYPE_ENTRY: "n1-standard-2",
                cl.GCP_STATE_FILE_DIR: None
                }
    parser = cl.get_core_args_parser('Handles instance creation, monitoring and shutdown on GCP')
    parser.add_argument("--sleep-duration", type=int, default=180, #TODO Bug here?
                        help='How many seconds to sleep between checking instance health')
    cl.get_full_args_parser("Handles instance creation, monitoring and shutdown on GCP",
                            wpt_location=False, gcp_instances=True)
    result, c = cl.get_config(fixed_config=vars(parser.parse_args()), default_config=defaults)
    if result:
        main(c)
    else:
        logging.critical("Invalid configuration. Quitting...")

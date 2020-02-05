import yaml
import logging
import os.path
import urllib.request
import urllib.error
import argparse

WPT_SERVER_URL_ENTRY = "wpt-server-url"
JOBS_DB_PATH_ENTRY = "jobs-db-path"
WPT_API_KEY_ENTRY = "wpt-api-key"
WPT_LOCATIONS_PATH_ENTRY = "wpt-locations-path"
GCP_CREDENTIALS_PATH_ENTRY = "gcp-credentials-path"
FILE_CONFIG_PATH_ENTRY = "file-config-path"


def get_known_config_keys():
    return {WPT_SERVER_URL_ENTRY, JOBS_DB_PATH_ENTRY, WPT_API_KEY_ENTRY,
            WPT_LOCATIONS_PATH_ENTRY, GCP_CREDENTIALS_PATH_ENTRY}


def url_is_alive(url):
    request = urllib.request.Request(url)
    request.get_method = lambda: 'HEAD'
    try:
        urllib.request.urlopen(request)
        return True, None
    except urllib.error.HTTPError as E:
        return False, E
    except urllib.error.URLError as E:
        return False, E


def validate_config(config):
    success = True
    for k in get_known_config_keys():
        if k not in config.keys() and k is not FILE_CONFIG_PATH_ENTRY:
            logging.debug(f"{k} is not in the configuration")
    if WPT_SERVER_URL_ENTRY in config:  # TODO - Check the actual HEAD response is correct
        condition, result = url_is_alive(config[WPT_SERVER_URL_ENTRY])
        if not condition:
            logging.critical(f"Could not  reach wpt server at {config[WPT_SERVER_URL_ENTRY]}. Error: {result.reason}")
            success = False
    if JOBS_DB_PATH_ENTRY in config:
        if not os.path.isfile(config[JOBS_DB_PATH_ENTRY]):
            logging.warning(f"Jobs db file does not exist at {config[JOBS_DB_PATH_ENTRY]}")
    if WPT_API_KEY_ENTRY in config.keys():
        if len(config[WPT_API_KEY_ENTRY]) != 32:  # TODO Check this is actually the correct length!
            logging.critical("The wpt-api-key is the wrong length.")
            success = False
    if WPT_LOCATIONS_PATH_ENTRY in config:
        if not os.path.isfile(config[WPT_LOCATIONS_PATH_ENTRY]):
            logging.critical(f"WPT locations file does not exist at {config[WPT_LOCATIONS_PATH_ENTRY]}")
            success = False
    if GCP_CREDENTIALS_PATH_ENTRY in config:
        if not os.path.isfile(config[GCP_CREDENTIALS_PATH_ENTRY]):
            logging.critical(f"GCP credentials file does not exist at {config[WPT_LOCATIONS_PATH_ENTRY]}")
            success = False
    return success


def get_config(fixed_config=None, default_config=None):
    """
    :param fixed_config: Configuration options which cannot be overwritten
    :param default_config: Configuration options which will be overwritten if a config file is present
    :return: Boolean (whether the config is valid), the config as a dictionary
    """
    if default_config is None:
        default_config = dict()
    if fixed_config is None:
        fixed_config = dict()
    file_config_path = None
    if FILE_CONFIG_PATH_ENTRY in fixed_config.keys():
        file_config_path = fixed_config[FILE_CONFIG_PATH_ENTRY]
    elif FILE_CONFIG_PATH_ENTRY in default_config.keys():
        file_config_path = default_config[FILE_CONFIG_PATH_ENTRY]
    if file_config_path is not None:
        logging.info(f"Looking for config file at path: {file_config_path}")
        file_config = get_file_config(file_config_path)
        file_overridden_keys = set(fixed_config.keys()).intersection(set(file_config.keys()))
        if len(file_overridden_keys) > 0:
            logging.warning(f"The following file config keys are being overridden: f{file_overridden_keys}")
        file_config.update(fixed_config)  # Fixed config overwrites file config
        default_config.update(file_config)  # File/Fixed config overwrites default config
        config = default_config
    else:
        logging.debug("No config file was specified.")
        default_used = set(default_config.keys()).difference(set(fixed_config.keys()))
        if len(default_used) > 0:
            logging.warning(f"Default config values were used for the following config keys: f{default_used}")
        config = default_config.update(fixed_config)
    if validate_config(config):
        return True, config
    else:
        return False, None


def get_file_config(file):
    if not os.path.isfile(file):
        logging.info(f"No config file at provided path: {file}")
        return dict()
    logging.debug(f"Attempting to load config from {file}")
    with open(file, 'r') as stream:
        config = yaml.safe_load(stream)
    logging.debug(f"Loaded the following configuration from {file} \n {config}")
    if not set(config.keys()).issubset(get_known_config_keys()):
        # TODO There is probably a better way to do this, as this does not check inner structure, types, etc.
        logging.critical(
            f"Unrecognised configuration keys in {file}: \n {set(config.keys()) - get_known_config_keys()}")
    return config


def add_wpt_args(parser):
    parser.add_argument("--wpt-server", metavar='URL', type=str, help='The URL for the WPT Server',
                        dest=WPT_SERVER_URL_ENTRY)
    parser.add_argument("--wpt-key", metavar='SECRET', type=str, help='The API Key for the WPT Server',
                        dest=WPT_API_KEY_ENTRY)
    return parser


def add_wpt_location_args(parser):
    parser.add_argument("--wpt-locations", metavar='PATH', type=str,
                        help='The path to the locations.ini file for the WPT Server', dest=WPT_LOCATIONS_PATH_ENTRY)
    return parser


def add_gcp_args(parser):
    parser.add_argument("--gcp-secret", metavar='PATH', type=str, help="The path to the credentials file for GCP",
                        dest=GCP_CREDENTIALS_PATH_ENTRY)


def add_jobs_args(parser):
    parser.add_argument("--job-db", metavar='PATH', type=str, help="The path to the Job DB",
                        dest=JOBS_DB_PATH_ENTRY)


def get_core_args_parser(description):
    parser = argparse.ArgumentParser(description=description, argument_default=argparse.SUPPRESS)
    parser.add_argument("--config-file", metavar='PATH', type=str, help="The path to the config file",
                        dest=FILE_CONFIG_PATH_ENTRY)
    return parser


def get_full_args_parser(description, wpt_location=False):
    parser = get_core_args_parser(description)
    add_jobs_args(parser)
    add_gcp_args(parser)
    add_wpt_args(parser)
    if wpt_location:
        add_wpt_location_args(parser)
    return parser


""" 
Typical usage:
Set some defaults and a description. If something is *required* but not known, set the default as None. 
get a args parser (either full or with some subset). 
customise it with any additional settings.
Parse the arguments. 
get_config with the arguments, then the defaults. 
Check the result and use if it if successful
"""

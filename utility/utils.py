""" This library file holds functions that don't fit in other locations.
"""

from glob import glob
import json
import bz2
import os
import urllib.request
from urllib.error import HTTPError
import logging

SEPERATOR = "--"


def zone_from_name(name):
    components = name.split(SEPERATOR)
    return components[0]


def id_from_name(name):
    components = name.split(SEPERATOR)
    return components[2]


def location_to_dict(location):
    components = location.split(SEPERATOR)
    row = dict()
    row['zone'] = components[0]
    row['browser'] = components[1]
    row['agent_id'] = components[2]
    return row


def dict_to_location(row):
    """ Turns a GCP Location into a WPT Location. 
    """
    return row['zone'] + SEPERATOR + row['browser'] + SEPERATOR + row['agent_id']


def gather_scripts(folder, suffix='.wpt'):
    """ Gathers all WPT Script files from a directory (recursively)

    Parameters:
        Folder - The folder to recursively search 
        Suffix - The suffix for WPT script files. 
    """
    scripts = glob(folder + '/**/*' + suffix, recursive=True)
    logging.debug("Discovered {lenScripts} test scripts in {folder}".format(lenScripts=len(scripts), folder=folder))
    return {os.path.split(os.path.splitext(s)[0])[1]: s for s in scripts}


def gather_compressed_results(folder, suffix='.bz2'):
    """ Gathers all WPT Results files from a directory (recursively)

    Parameters:
        Folder - The folder to recursively search 
        Suffix - The suffix for WPT Results files. 
    """
    results = glob(folder + '/**/*' + suffix, recursive=True)
    logging.debug(
        "Discovered {lenScripts} compressed results in {folder}".format(lenScripts=len(results), folder=folder))
    return results


def gather_and_load_results(folder):
    """ Loads all WPT Result files from a directory (recursively) into memory

    Parameters:
        Folder - The folder to recursively search 

    Output: A list results, each result is a Python dictionary.
    """
    results = gather_compressed_results(folder)
    return list(map(load_result, results))


def script_to_string(p):
    """ Given a script file, load it as a string
    """
    f = open(p, 'r')
    s = f.read()
    return s


def save_result(result, results_folder='out'):
    """  Given a result, extract key data, compress it and store it
    """
    test_id = result['data']['id']
    label = result['data']['label']
    label = label.replace('..', '')
    test_folder = results_folder + '/' + label + '-' + test_id
    logging.debug(f"Saving result with id {test_id} and label {label} to {test_folder}")
    os.makedirs(test_folder, exist_ok=True)
    f = open(test_folder + '/results.json.bz2', 'wb')
    result_str = json.dumps(result).encode('utf-8')
    f.write(bz2.compress(result_str))
    f.close()
    urls = list()
    errors = list()
    for run_number, run_result in result['data']['runs'].items():
        if 'steps' not in run_result['firstView'].keys():
            urls.append((run_number, 0, run_result['firstView']['images']['screenShot']))
            continue
        for step_number, step_result in enumerate(run_result['firstView']['steps']):
            urls.append((run_number, step_number, step_result['images']['screenShot']))
    logging.debug("Discovered {lenURLs} for {test_id} labelled {label}".format(
        lenURLs=len(urls), test_id=test_id, label=label))
    for run_number, step_number, url in urls:
        screenshot_name = 'R' + str(run_number) + 'S' + str(step_number) + '.jpg'
        try:
            urllib.request.urlretrieve(url, filename=test_folder + '/' + screenshot_name)
        except HTTPError as E:
            logging.warning(f"Error {E} fetching URL: {url}")
            errors.append(str(E))
        return len(errors) > 0, test_folder, errors


def load_result(result):
    """ Given a result file, decompress it and load the object into memory. 
    """
    logging.debug(f"Loading the result at {result}")
    f = open(result, 'rb')
    s = bz2.decompress(f.read())
    f.close()
    try:
        j = json.loads(s)
    except json.JSONDecodeError as E:
        logging.warning(f"Error {E} decoding {result}")
        return None
    return j

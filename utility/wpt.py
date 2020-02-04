""" Library file for functions that interact with the WPT server.
"""

import json
import subprocess
from tempfile import SpooledTemporaryFile
import utils
import logging
from typing import Sequence


def _get_buffered_json(command: Sequence[str]):
    temp_out_file = SpooledTemporaryFile(mode='w+')
    # noinspection PyTypeChecker
    result = subprocess.run(command, stdout=temp_out_file, bufsize=4096, check=True)
    assert (result.returncode == 0)
    temp_out_file.seek(0)  # Have to return to the start of the file to read it.
    result = temp_out_file.read()
    temp_out_file.close()
    output = json.loads(result)  # String to JSON
    return output


def _successful_result(result):
    """ Checks that a WPT test was successful.

    Returns a boolean value indicating success or failure.

    Parameters:
        result - A result returned from the WPT API converted into a python object.

    """
    return result['statusCode'] == 200 and result['statusText'] == 'Test Complete'


class WPT:
    def __init__(self, server, key, locations_file=None):
        self.server = server
        self.key = key
        self.locations_file = locations_file  # '/var/www/webpagetest/www/settings/locations.ini'
        self.temp_locations_file = 'newLocations.ini'
        self.logger = logging.getLogger("utility." + __name__)
        self.logger.debug("Initialised logging for WPT Object attached to server {s}".format(s=server))
        if locations_file is None:
            self.logger.debug("There is no location file set")
        else:
            self.logger.debug("Path to Location file:{p}".format(p=locations_file))

    def run_test(self, path, location, connectivity='Native'):
        """ Synchronously run a WPT test and return the output.

        This function calls the WPT javascript API and submits a test. It polls
        (every 5 seconds) for the job to finish and returns the results as an object
        (parsed from the JSON).

        Positional Arguments:
            path - The location of the script to test, or the website URL
            server - The WPT server to use
            key - The API key for the WPT server

        Keyword Arguments:
            connectivity - The connectivity profile to use for the test
            location - The location that should run the test.
        """
        self.logger.debug("Synchronously running a test on {p} with location {l} and connectivity {c}".format(
            p=path, l=location, c=connectivity)
        )
        args = [
            'webpagetest',
            'test', path,
            '--server', self.server,
            '--key', self.key,
            '--location', location,
            '--runs', '1',
            '--connectivity', connectivity,
            '--label', path,
            '--keepua',  # Don't change the useragent to indicate this is a bot
            '--first',  # Don't try for a repeat view
            '--poll', '5'  # How frequently to poll the web server for the result
        ]
        return _get_buffered_json(args)

    def submit_test(self, job):
        """ Asynchronously run a WPT test.

        This function calls the WPT javascript API and submits a test. It returns the result
        of the request as an object, including success code and a unique ID for the submitted
        job.
        """
        if "location" not in job.keys():
            job["location"] = utils.dict_to_location(job)
        self.logger.debug("Asynchronously running a test labelled {job_id} on {script} with location {location},"
                          " {runs} runs, connectivity {connectivity}".format_map(job))
        args = [
            'webpagetest',
            'test', job['script'],
            '--server', self.server,
            '--key', self.key,
            '--location', job["location"],
            '--runs', job["runs"],
            '--connectivity', job["connectivity"],
            '--label', job['job_id'],
            '--keepua',  # Don't change the useragent to indicate this is a bot
            '--first',  # Don't try for a repeat view
        ]
        result = _get_buffered_json(args)
        if _successful_result(result):
            queue_id = result['data']['testId']
            return True, queue_id
        else:
            return False, "ERROR MESSAGE NOT YET IMPLEMENTED"  # TODO return the error from the response

    def run_and_save_test(self, path, location,connectivity):
        """ Runs a WPT test (synchronously), checks the result and saves it
        """
        r = self.run_test(path, location, connectivity)
        if not _successful_result(r):
            logging.warning("Synchronous test failed for {path} on location {location} with connectivity"
                            "{connectivity}. The result was {r} "
                            .format(path=path, location=location, connectivity=connectivity, r=r))
        utils.save_result(r)

    def get_testers(self):
        args = ['webpagetest',
                'testers',
                '--server',
                self.server
                ]
        self.logger.debug("Fetching the testers from the WPT Server")
        return _get_buffered_json(args)

    def get_locations(self):
        # See which locations the server thinks are up.
        # Check all active instances appear on this list
        # Its okay if the server thinks some locations are up but the instances are down. It just hasn't realised yet.
        args = ['webpagetest',
                'locations',
                '--server',
                self.server
                ]
        self.logger.debug("Fetching the locations from the WPT Server")
        return _get_buffered_json(args)

    def get_job_queues(self):
        q = self.get_locations()
        if 'data' not in q['response'].keys():
            # No queues up!
            return dict()
        result = dict()
        if isinstance(q['response']['data']['location'], list):
            for v in q['response']['data']['location']:
                result[v['id']] = v['PendingTests']['Total']
        else:
            return {
                q['response']['data']['location']['id']:
                    q['response']['data']['location']['PendingTests']['Total']
            }
        self.logger.debug("There are {locationLen} queues on the server".format(locationLen=len(result.keys())))
        return result

    def get_active_job_queues(self):
        return [k for (k, v) in self.get_job_queues().items() if v > 0]

    def set_server_locations(self, locations):
        assert (self.temp_locations_file is not None)
        assert (self.locations_file is not None)
        self.logger.info("Updating the location file at {p} with {l} locations"
                          .format(p=self.locations_file,l=len(locations)))
        self.logger.debug("Using {t} as the temporary file".format(t=self.temp_locations_file))
        f = open(self.temp_locations_file, 'w')
        data = """[locations]
    1=Test_loc
    default=Test_loc
      
    [Test_loc]
    1=TESTLOCATIONCHANGEME
    """
        count = 1
        for location in locations:
            count += 1
            data += str(count) + "=" + location + "\n"
        data += 'label="Test Location"\n'
        data += """
    [TESTLOCATIONCHANGEME]
    browser=Chrome,Firefox,Tor Browser
    label="Test Location"
    
    """
        for location in locations:
            data += "[" + location + "]" + "\n"
            if 'tor' in location:
                data += "browser=Tor Browser\n"
            else:
                data += "browser=Firefox\n"
            data += 'label="' + location + '"\n'
            data += '\n'
        f.write(data)
        f.close()
        args = [
            'cp',
            self.temp_locations_file,
            self.locations_file
        ]
        return subprocess.run(args)

    def check_test_finished(self, test_id):
        args = ['webpagetest',
                'status',
                test_id,
                '--server',
                self.server
                ]
        self.logger.debug(f"Checking the status of test id: {test_id}")
        output = _get_buffered_json(args)
        if _successful_result(output):
            return True
        else:
            return False

    def get_test_result(self, test_id):
        self.logger.debug(f"Fetching the results for test id: {test_id}")
        args = ['webpagetest',
                'results',
                test_id,
                '--server',
                self.server
                ]
        return _get_buffered_json(args)

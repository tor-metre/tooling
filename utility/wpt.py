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

    def submit_test(self, job, connectivity='Native'):
        """ Asynchronously run a WPT test.

        This function calls the WPT javascript API and submits a test. It returns the result
        of the request as an object, including success code and a unique ID for the submitted
        job.

        Positional Arguments:
            job - A python dictionary containing a 'script' key with a string value
            server - The WPT server to use
            key - The API key for the WPT server
        """
        location = utils.rowToLocation(job)
        args = [
            'webpagetest',
            'test', job['script'],
            '--server', self.server,
            '--key', self.key,
            '--location', location,
            '--runs', '1',
            '--connectivity', connectivity,
            '--label', job['script'],
            '--keepua',  # Don't change the useragent to indicate this is a bot
            '--first',  # Don't try for a repeat view
        ]
        return _get_buffered_json(args)

    def run_and_save_test(self, path, location):
        """ Runs a WPT test (synchronously), checks the result and saves it
        """
        r = self.run_test(path, location)
        if not _successful_result(r):
            logging.warning("Task Failed: " + r['statusText'])
        utils.saveResults(r)

    def get_testers(self):
        args = ['webpagetest',
                'testers',
                '--server',
                self.server
                ]
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
        return result

    def get_active_job_queues(self):
        return [k for (k, v) in self.get_job_queues().items() if v > 0]

    def set_server_locations(self, locations):
        assert (self.temp_locations_file is not None)
        assert (self.locations_file is not None)
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
        output = _get_buffered_json(args)
        if _successful_result(output):
            return True
        else:
            return False

    def get_test_result(self, test_id):
        args = ['webpagetest',
                'results',
                test_id,
                '--server',
                self.server
                ]
        return _get_buffered_json(args)

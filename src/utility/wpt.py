""" Library file for functions that interact with the WPT server.
"""

import json
import subprocess
from tempfile import SpooledTemporaryFile
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


def is_successful_result(result):
    """ Checks that a WPT test was successful.

    Returns a boolean value indicating success or failure.

    Parameters:
        result - A result returned from the WPT API converted into a python object.

    """
    return result['statusCode'] == 200 and (result['statusText'] == 'Test Complete' or result['statusText'] == 'Ok')


class WPT:
    # WARNING - This class is NOT Thread Safe

    def __init__(self, server, key, locations_file=None):
        self.server = server
        self.key = key
        self.locations_file = locations_file  # '/var/www/webpagetest/www/settings/locations.ini'
        self.temp_locations_file = 'newLocations.ini'
        self.logger = logging.getLogger("utility." + __name__)
        self.logger.debug(f"Initialised logging for WPT Object attached to server {server}")
        if locations_file is None:
            self.logger.debug("There is no location file set")
        else:
            self.logger.debug(f"Path to Location file:{locations_file}")

    def submit_test(self, job):
        """ Asynchronously run a WPT test.

        This function calls the WPT javascript API and submits a test. It returns the result
        of the request as an object, including success code and a unique ID for the submitted
        job.
        """
        args = [
            'webpagetest',
            'test', job.target,
            '--server', self.server,
            '--key', self.key,
            '--location', job.instance.wpt_location,
            '--label', job.description
            #'--keepua',  # Don't change the useragent to indicate this is a bot
            #'--first',  # Don't try for a repeat view
        ]
        args.extend(job.get_options_list())
        result = _get_buffered_json(args)
        if is_successful_result(result):
            queue_id = result['data']['testId']
            return True, queue_id
        else:
            return False, result  # TODO return the error from the response

    def get_testers(self):
        args = ['webpagetest',
                'testers',
                '--server',
                self.server
                ]
        self.logger.debug("Fetching the testers from the WPT Server")
        return _get_buffered_json(args)

    def get_online_locations(self):
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

    def get_job_locations(self):
        q = self.get_online_locations()
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
        self.logger.debug(f"There are {len(result.keys())} locations on the server")
        return result

    def get_busy_locations(self):
        return [k for (k, v) in self.get_job_locations().items() if v > 0]

    #TODO Think about using the Experiment Field to separate instances?
    def set_server_locations(self, locations):
        #Expects an instance!
        assert (self.temp_locations_file is not None)
        assert (self.locations_file is not None)
        self.logger.info(f"Updating the location file at {self.locations_file} with {len(locations)} locations")
        self.logger.debug(f"Using {self.temp_locations_file} as the temporary file")
        f = open(self.temp_locations_file, 'w')
        data = """
[locations]
1=Test_loc
default=Test_loc
      
[Test_loc]
1=TESTLOCATIONCHANGEME
"""
        count = 1
        for location in locations:
            count += 1
            data += str(count) + "=" + location.wpt_location + "\n"
        data += """label="Test Location"

[TESTLOCATIONCHANGEME]
browser=Chrome,Firefox,Tor Browser
label="Test Location"

"""
        for location in locations:
            data += "[" + location.wpt_location + "]" + "\n"
            data += "browser=Tor Browser,Firefox\n"
            if location.description is None:
                data += 'label="' + 'No Description' + '"\n'
            else:
                data += 'label="' + location.description + '"\n'
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
        if is_successful_result(output):
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
        r = _get_buffered_json(args)
        if is_successful_result(r):
            return True, r['data']['summary']
        else:
            return False, r
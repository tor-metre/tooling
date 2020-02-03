""" Library file for functions that interact with the WPT server.
"""

import json
import subprocess
from tempfile import SpooledTemporaryFile
import utils
import logging


class WPT:
    def __init__(self, server, key, locations_file=None):
        self.server = server
        self.key = key
        self.locations_file = locations_file  # '/var/www/webpagetest/www/settings/locations.ini'
        self.temp_locations_file = 'newLocations.ini'

    def _getBufferedJSON(self, command):
        outT = SpooledTemporaryFile(mode='w+')
        result = subprocess.run(command, stdout=outT, bufsize=4096, check=True)
        assert(result.returncode == 0)
        outT.seek(0)  # Have to return to the start of the file to read it.
        result = outT.read()
        outT.close()
        output = json.loads(result)  # String to JSON
        return output

    def runTest(self, path, location, connectivity='Native'):
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
        return self._getBufferedJSON(args)

    def submitTest(self, job, connectivity='Native'):
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
        return self._getBufferedJSON(args)

    def successfulResult(self, result):
        """ Checks that a WPT test was successful.

        Returns a boolean value indicating success or failure.

        Parameters:
            result - A result returned from the WPT API converted into a python object.

        """
        return result['statusCode'] == 200 and result['statusText'] == 'Test Complete'

    def runTask(self, path, location):
        """ Runs a WPT test (synchronously), checks the result and saves it
        """
        r = self.runTest(path, location)
        if not self.successfulResult(r):
            logging.warning("Task Failed: " + r['statusText'])
        utils.saveResults(r)

    def getTesters(self):
        args = ['webpagetest',
                'testers',
                '--server',
                self.server
                ]
        return self._getBufferedJSON(args)

    def getQueueStatus(self):
        # See which locations the server thinks are up.
        # Check all active instances appear on this list
        # Its okay if the server thinks some locations are up but the instances are down. It just hasn't realised yet.
        args = ['webpagetest',
                'locations',
                '--server',
                self.server
                ]
        return self._getBufferedJSON(args)

    def getQueuedJobs(self):
        q = self.getQueueStatus()
        if 'data' not in q['response'].keys():
            # No queues up!
            return dict()
        result = dict()
        if isinstance(q['response']['data']['location'], list):
            for v in q['response']['data']['location']:
                l = v['id']
                t = v['PendingTests']['Total']
                result[l] = t
        else:
            return {
                q['response']['data']['location']['id']:
                    q['response']['data']['location']['PendingTests']['Total']
            }
        return result

    def getActiveQueues(self):
        return [k for (k, v) in self.getQueuedJobs().items() if v > 0]

    def setServerLocations(self, locations):
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
        for l in locations:
            count += 1
            data += str(count) + "=" + l + "\n"
        data += 'label="Test Location"\n'
        data += """
    [TESTLOCATIONCHANGEME]
    browser=Chrome,Firefox,Tor Browser
    label="Test Location"
    
    """
        for l in locations:
            data += "[" + l + "]" + "\n"
            if 'tor' in l:
                data += "browser=Tor Browser\n"
            else:
                data += "browser=Firefox\n"
            data += 'label="' + l + '"\n'
            data += '\n'
        f.write(data)
        f.close()
        args = [
            'cp',
            self.temp_locations_file,
            self.locations_file
        ]
        return subprocess.run(args)

    def checkFinished(self, id):
        args = ['webpagetest',
                'status',
                id,
                '--server',
                self.server
                ]
        output = self._getBufferedJSON(args)
        if int(output['statusCode']) == 200:
            return True
        else:
            return False

    def getResult(self, id):
        args = ['webpagetest',
                'results',
                id,
                '--server',
                self.server
                ]
        return self._getBufferedJSON(args)

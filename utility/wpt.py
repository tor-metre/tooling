""" Library file for functions that interact with the WPT server.
"""

import json
import subprocess
import tempfile
import utils
import gcp

def runTest(path,server,key,connectivity='Native',location='firefox'):
    """ Sychronously run a WPT test and return the output.

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
        '--server', server,
        '--key', key,
        '--location', location,
        '--runs', '1',
        '--connectivity', connectivity,
        '--label',path,
        '--keepua', #Don't change the useragent to indicate this is a bot
        '--first', #Don't try for a repeat view
        '--poll','5' #How frequently to poll the web server for the result
    ]
    outT = tempfile.SpooledTemporaryFile(mode='w+') 
    result = subprocess.run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = json.loads(result) #String to JSON
    return output  

def submitTest(job,server,key):
    """ Asychronously run a WPT test.

    This function calls the WPT javascript API and submits a test. It returns the result
    of the request as an object, including success code and a unique ID for the submitted
    job.

    Positional Arguments:
        job - A python dictionary containing a 'script' key with a string value
        server - The WPT server to use
        key - The API key for the WPT server
    """
    location = gcp.rowToLocation(job)
    args = [
        'webpagetest',
        'test', job['script'],
        '--server', server,
        '--key', key,
        '--location', location,
        '--runs', '1',
        '--connectivity', 'Native',
        '--label',job['script'],
        '--keepua', #Don't change the useragent to indicate this is a bot
        '--first', #Don't try for a repeat view
    ]
    outT = tempfile.SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    result = subprocess.run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = json.loads(result) #String to JSON
    return output

def successfulResult(result):
    return result['statusCode'] == 200 and result['statusText'] == 'Test Complete'

def runTask(path,location):
    r = runTest(path,location=location)
    if not successfulResult(r):
        logging.warning("Task Failed: " + r['statusText'] )
    utils.saveResults(r)